from django import forms
from django.core.exceptions import ValidationError
from .models import Product, Variant, ProductImage
from django.forms.widgets import ClearableFileInput
from .constants import CATEGORIES, CONDITIONS, STATUSES, VINTED_FEE_PERCENT, VINTED_FIXED_FEE
from decimal import Decimal, ROUND_HALF_UP

class MultiFileInput(ClearableFileInput):
    allow_multiple_selected = True

class ProductForm(forms.ModelForm):
    category = forms.CharField(max_length=120)
    class Meta:
        model = Product
        fields = ['main_sku','name','brand','category']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Main SKU optional and normalized
        self.fields['main_sku'].required = False
        self.fields['main_sku'].help_text = 'Optional. Leave blank to auto-generate (e.g., 001).'

    def clean_main_sku(self):
        sku = (self.cleaned_data.get('main_sku') or '').strip()
        if not sku:
            return sku
        if sku.isdigit():
            sku = f"{int(sku):03d}"
        qs = Product.objects.filter(main_sku=sku)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Main SKU already in use.')
        return sku

class VariantForm(forms.ModelForm):
    images = forms.FileField(widget=MultiFileInput(attrs={'multiple': True}), required=False)
    condition = forms.ChoiceField(choices=[(c, c) for c in CONDITIONS])
    status = forms.ChoiceField(choices=[(s, s) for s in STATUSES])
    class Meta:
        model = Variant
        fields = ['variant_sku','size','condition','colour','date','cost','price','fees','qty','location','status']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Fees optional; auto-calculated if missing
        self.fields['fees'].required = False
        # Variant SKU optional, normalized
        self.fields['variant_sku'].required = False
        self.fields['variant_sku'].help_text = 'Optional. Leave blank to auto-generate (e.g., HOOD-XL-001).'
        # Make most fields optional to ease quick add; rely on model defaults
        for fname in ['size','condition','colour','date','cost','price','qty','location','status']:
            if fname in self.fields:
                self.fields[fname].required = False
        # Provide sensible initials
        self.fields.get('status', None) and self.fields.__getitem__('status').widget and self.fields.__getitem__('status').widget.attrs.update({'data-initial':'Draft'})
        # Ensure existing values appear even if not in configured lists
        if self.instance and self.instance.pk:
            cur_cond = (self.instance.condition or '').strip()
            cur_stat = (self.instance.status or '').strip()
            if cur_cond and cur_cond not in CONDITIONS:
                self.fields['condition'].choices = [(cur_cond, cur_cond)] + self.fields['condition'].choices
            if cur_stat and cur_stat not in STATUSES:
                self.fields['status'].choices = [(cur_stat, cur_stat)] + self.fields['status'].choices
    def clean(self):
        cleaned = super().clean()
        price = cleaned.get('price')
        fees = cleaned.get('fees')
        # Auto-calc fees if not provided or zero
        if price is not None and (fees is None or fees == 0):
            try:
                auto_fees = (Decimal(price) * Decimal(VINTED_FEE_PERCENT)) + Decimal(VINTED_FIXED_FEE)
                # round to 2dp
                auto_fees = auto_fees.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                cleaned['fees'] = auto_fees
            except Exception:
                pass
        return cleaned

    def clean_variant_sku(self):
        sku = (self.cleaned_data.get('variant_sku') or '').strip()
        if not sku:
            return sku
        sku_norm = sku.upper().replace(' ', '')
        qs = Variant.objects.filter(variant_sku=sku_norm)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Variant SKU already in use.')
        return sku_norm

class ImportFileForm(forms.Form):
    file = forms.FileField(help_text="Upload a CSV or XLSX file matching the template.")
