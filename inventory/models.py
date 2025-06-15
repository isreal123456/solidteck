# inventory/models.py


from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from openpyxl.compat.product import product
from unicodedata import category


class Category(models.Model):
    name = models.CharField(max_length=100)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = 'categories'
    def __str__(self):
            return f'{self.name}'
    def get_product(self):
        product = Product.objects.filter(category_id=self.id)
        return product

class Product(models.Model):
    name = models.CharField(max_length=100)
    stock = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(default=timezone.now)  # ✅ Add this line


    def __str__(self):
        return f'{self.name}--{self.category}'
