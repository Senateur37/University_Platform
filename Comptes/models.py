# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ("student", "Étudiant"),
        ("teacher", "Enseignant"),
        ("admin", "Administrateur"),
    ]
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    is_validated = models.BooleanField(default=False)  # validation manuelle ou automatique
    # éventuellement : promotion, filière, etc.