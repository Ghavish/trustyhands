from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # Defining the roles from your TrustyHands architecture
    ROLE_CHOICES = (
        ('CLIENT', 'Client'),
        ('PROVIDER', 'Service Provider'),
        ('ADMIN', 'Admin'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CLIENT')

    def __str__(self):
        return self.username