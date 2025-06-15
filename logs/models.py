# inventory/models.py

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Log(models.Model):
    user = models.ForeignKey(User,on_delete=models.DO_NOTHING)
    log = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.log[:100]
