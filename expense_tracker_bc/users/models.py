from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.




class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin')
    )
    role = models.CharField(max_length=5, choices=ROLE_CHOICES, default='user')
