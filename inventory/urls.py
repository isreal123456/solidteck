from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory_view, name='inventory'),
    path('category/<int:pk>/prodouct', views.product_view, name='product'),

    # Category URLs
    path('category/create/', views.create_category, name='create_category'),
    path('category/<int:pk>/edit/', views.edit_category, name='edit_category'),
    path('category/<int:pk>/delete/', views.delete_category, name='delete_category'),

    # Product URLs
    path('product/create/', views.create_product, name='create_product'),
    path('product/<int:pk>/edit/', views.edit_product, name='edit_product'),
    path('product/<int:pk>/delete/', views.delete_product, name='delete_product'),
path('dashboard/', views.inventory_dashboard, name='inventory_dashboard'),


]
