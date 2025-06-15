from django.contrib import admin
from .models import Category, Product

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', )

# inventory/admin.py

from django.contrib import admin
from .models import Product


admin.site.register(Product, )

admin.site.register(Category, CategoryAdmin)
