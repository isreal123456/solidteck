# inventory/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from inventory.models import Category, Product
from logs.models import Log

# --- Category signals ---

@receiver(post_save, sender=Category)
def log_category_save(sender, instance, created, **kwargs):
    if created:
        msg = f'created a category "{instance.name}"'

    else:
        msg = f'updated category "{instance.name}"'
    Log.objects.create(
        user=getattr(instance, 'created_by', None),  # ✅ fix here
        log=msg
    )

@receiver(post_delete, sender=Category)
def log_category_delete(sender, instance, **kwargs):
    msg = f'deleted category "{instance.name}"'
    Log.objects.create(
        user=getattr(instance, 'created_by', None),  # ✅ fix here
        log=msg
    )

# --- Product signals ---

@receiver(post_save, sender=Product)
def log_product_save(sender, instance, created, **kwargs):
    action = "created" if created else "updated"
    Log.objects.create(
        user=getattr(instance, "created_by", None),
        log=f'Product "{instance.name}" was {action} in category "{instance.category.name}".'
    )

@receiver(post_delete, sender=Product)
def log_product_delete(sender, instance, **kwargs):
    Log.objects.create(
        user=getattr(instance, "created_by", None),
        log=f'Product "{instance.name}" was deleted from category "{instance.category.name}".'
    )
