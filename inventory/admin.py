from django.contrib import admin
from .models import Product, Variant, ProductImage

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class VariantInline(admin.TabularInline):
    model = Variant
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('main_sku','name','brand','category','created_at')
    search_fields = ('main_sku','name','brand')
    inlines = [VariantInline]

@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ('variant_sku','product','size','condition','price','status')
    search_fields = ('variant_sku','product__name')
    inlines = [ProductImageInline]

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('variant','uploaded_at')
