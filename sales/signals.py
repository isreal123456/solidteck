# sales/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Order, OrderItem
from logs.models import Log  # adjust path if Log is elsewhere

@receiver(post_save, sender=Order)
def log_order_created_or_updated(sender, instance, created, **kwargs):
    user = instance.sold_by
    if created:
        Log.objects.create(user=user, log=f"🧾 Created Order #{instance.id} for {instance.customer_name} by {user}")
    else:
        Log.objects.create(user=user, log=f"✏️ Updated Order #{instance.id}")

@receiver(post_delete, sender=Order)
def log_order_deleted(sender, instance, **kwargs):
    Log.objects.create(user=instance.sold_by, log=f"🗑️ Deleted Order #{instance.id} for {instance.customer_name}")

@receiver(post_save, sender=OrderItem)
def log_orderitem_created_or_updated(sender, instance, created, **kwargs):
    user = instance.order.sold_by
    product_name = instance.product.name
    if created:
        Log.objects.create(user=user, log=f"➕ Added {instance.quantity} x {product_name} to Order #{instance.order.id}")
    else:
        Log.objects.create(user=user, log=f"✏️ Updated {product_name} in Order #{instance.order.id}")

@receiver(post_delete, sender=OrderItem)
def log_orderitem_deleted(sender, instance, **kwargs):
    user = instance.order.sold_by
    Log.objects.create(user=user, log=f"🗑️ Removed {instance.product.name} from Order #{instance.order.id}")
