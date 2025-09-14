from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
from .constants import VINTED_FEE_PERCENT, VINTED_FIXED_FEE

CONDITION_CHOICES = None  # handled via forms (configurable)
STATUS_CHOICES = None     # handled via forms (configurable)

class Product(models.Model):
    main_sku = models.CharField(max_length=10, unique=True, blank=True)
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=120, blank=True)
    category = models.CharField(max_length=120, default='Clothing')
    archived = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.main_sku or '???'} — {self.name}"

    def save(self, *args, **kwargs):
        # Auto-generate main SKU (001, 002, ...) if not provided
        if not self.main_sku:
            last = Product.objects.order_by('-id').first()
            next_num = 1 if not last else (int(last.main_sku) if last.main_sku.isdigit() else last.id) + 1
            self.main_sku = f"{next_num:03d}"
        super().save(*args, **kwargs)

class Variant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    variant_sku = models.CharField(max_length=40, unique=True, blank=True)
    size = models.CharField(max_length=40, blank=True)
    condition = models.CharField(max_length=40, default='Good')
    colour = models.CharField(max_length=120, blank=True)
    date = models.DateField(default=timezone.now)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    net = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    margin = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # percent
    qty = models.PositiveIntegerField(default=1)
    location = models.CharField(max_length=120, default='Spare Room')
    status = models.CharField(max_length=20, default='Draft')

    def __str__(self):
        return f"{self.variant_sku or 'VAR?'}"

    def save(self, *args, **kwargs):
        # Auto-populate fees if not provided: fixed + percent of price
        if self.price is not None and (self.fees is None or self.fees == 0):
            try:
                self.fees = (self.price * Decimal(VINTED_FEE_PERCENT)) + Decimal(VINTED_FIXED_FEE)
            except Exception:
                # As a fallback do nothing; user can supply fees manually
                pass
        # Compute finance fields if possible
        if self.price is not None and self.fees is not None:
            self.net = (self.price - self.fees)
            self.profit = self.net - (self.cost or 0)
            self.margin = (self.profit / self.price * 100) if self.price else 0
        # Auto variant SKU: e.g. HOOD-XL-001 using category prefix + size + main sku
        if not self.variant_sku:
            cat_prefix = (self.product.category[:4] or 'ITEM').upper()
            size = (self.size or 'NA').upper()
            self.variant_sku = f"{cat_prefix}-{size}-{self.product.main_sku}"
        super().save(*args, **kwargs)

def product_image_path(instance, filename):
    return f"products/{instance.variant.product.main_sku}/{instance.variant.id}/{filename}"

class ProductImage(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=product_image_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
