from django.urls import path

from admin_panel import views

urlpatterns = [
path('', views.admin_dashboard, name='admin_dashboard'),
path('goodviewadmin', views.catergory_view, name='inventory_view_admin'),
path('goodviewadmin/<int:pk>/', views.product_view_admin, name='product_view'),
path('create_category_admin/', views.create_category_admin, name='create_category_admin'),
path('edit_category_admin/<int:pk>/', views.edit_category_admin, name='edit_category_admin'),
path('create_product_admin', views.create_product_admin, name='create_product_admin'),
path('edit_product_admin/<int:pk>/', views.edit_product_admin, name='edit_product_admin'),
path('delete_product_admin/<int:pk>/', views.delete_product_admin, name='delete_product_admin'),
path('delete_category_admin/<int:pk>/', views.delete_category_admin, name='delete_category_admin'),

path('order', views.order_list, name='list'),
path('createorderadmin/', views.create_order_admin, name='create_order_admin'),

    path('orders/<int:pk>/', views.order_detail, name='detail'),
path('admin-report/', views.admin_report, name='admin_report'),
    path('admin-report/export/excel/', views.export_admin_report_excel, name='export_admin_report_excel'),
    path('admin-report/export/pdf/', views.export_admin_report_pdf, name='export_admin_report_pdf'),
]