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
    is_validated = models.BooleanField(default=True)  # validation manuelle ou automatique
    bio = models.TextField(blank=True, verbose_name="Biographie")
    filiere = models.CharField(max_length=100, blank=True, verbose_name="Filière / Département")
    avatar = models.FileField(upload_to="avatars/", null=True, blank=True)

    @property
    def is_teacher_or_admin(self):
        if not self.is_authenticated:
            return False
        return self.is_superuser or self.is_staff or self.user_type in ['teacher', 'admin']

    def save(self, *args, **kwargs):
        if (self.is_superuser or self.is_staff) and not self.user_type:
            self.user_type = 'admin'
        super().save(*args, **kwargs)


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('announcement', 'Annonce'),
        ('assignment', 'Mission'),
        ('forum', 'Forum'),
        ('grade', 'Note'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='announcement')
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notification_type}] {self.title} -> {self.recipient.username}"