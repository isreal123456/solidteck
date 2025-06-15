# core/urls.py

from django.urls import path
from .views import log_list_view

urlpatterns = [
    path('logs/', log_list_view, name='log_list'),
]
