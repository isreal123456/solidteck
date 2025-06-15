from django.urls import path
from . import views

urlpatterns = [
    # --- Orders ---
    path('orders/', views.order_list, name='order_list'),
    path('orders/create/', views.create_order, name='create_order'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),

    # --- Dashboard ---
    path('dashboard/', views.dashboard, name='dashboard_sale'),

    # --- Sales Report ---
    path('sales/report/', views.sales_report, name='sales_report'),

    # --- Export Data ---
    path('export/excel/', views.export_orders_excel, name='export_orders_excel'),
    path('export/pdf/', views.export_orders_pdf, name='export_orders_pdf'),
    path('sales/export/excel/', views.export_sales_excel, name='export_sales_excel'),
    path('sales/export/pdf/', views.export_sales_pdf, name='export_sales_pdf'),
]
