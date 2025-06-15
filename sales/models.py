from django.conf import settings
from django.db import models
from django.db.models import Sum
from inventory.models import Product

class Order(models.Model):
    customer_name = models.CharField(max_length=200)
    sold_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_amount(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def total_item(self):
        return self.items.aggregate(total=Sum('quantity'))['total'] or 0

    def __str__(self):
        return f"Order #{self.id} by {self.sold_by}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    @property
    def total_price(self):
        return self.product.price * self.quantity
