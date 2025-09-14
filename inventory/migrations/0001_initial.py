# Generated initial migration for inventory app
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.core.validators import MinValueValidator

class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('main_sku', models.CharField(blank=True, max_length=10, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('brand', models.CharField(blank=True, max_length=120)),
                ('category', models.CharField(default='Clothing', max_length=120)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Variant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('variant_sku', models.CharField(blank=True, max_length=40, unique=True)),
                ('size', models.CharField(blank=True, max_length=40)),
                ('condition', models.CharField(choices=[('Like New', 'Like New'), ('Good', 'Good'), ('Fair', 'Fair'), ('Defective / Poor', 'Defective / Poor')], default='Good', max_length=40)),
                ('colour', models.CharField(blank=True, max_length=120)),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('cost', models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[MinValueValidator(0)])),
                ('price', models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[MinValueValidator(0)])),
                ('fees', models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[MinValueValidator(0)])),
                ('net', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('profit', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('margin', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('qty', models.PositiveIntegerField(default=1)),
                ('location', models.CharField(default='Spare Room', max_length=120)),
                ('status', models.CharField(choices=[('Draft', 'Draft'), ('Listed', 'Listed'), ('Sold', 'Sold')], default='Draft', max_length=20)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='inventory.product')),
            ],
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('variant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='inventory.variant')),
            ],
        ),
    ]
