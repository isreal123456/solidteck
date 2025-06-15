from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin_panel', 'Administrator'),
        ('storekeeper', 'Store Keeper'),
        ('salesperson', 'Sales Person')
    )
    role = models.CharField(max_length=40, choices=ROLE_CHOICES)

    def is_admin(self):
        return self.role == 'admin_panel'

    def is_storekeeper(self):
        return self.role == 'storekeeper'

    def is_salesperson(self):
        return self.role == 'salesperson'
