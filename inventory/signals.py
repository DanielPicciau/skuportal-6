from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Product, Variant
from .csv_sync import schedule_csv_sync


@receiver(post_save, sender=Product)
def _product_saved(sender, instance, **kwargs):
    schedule_csv_sync()


@receiver(post_delete, sender=Product)
def _product_deleted(sender, instance, **kwargs):
    schedule_csv_sync()


@receiver(post_save, sender=Variant)
def _variant_saved(sender, instance, **kwargs):
    schedule_csv_sync()


@receiver(post_delete, sender=Variant)
def _variant_deleted(sender, instance, **kwargs):
    schedule_csv_sync()

