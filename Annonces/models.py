# announcements/models.py
from django.db import models
from django.conf import settings
from Cours.models import Course

class Announcement(models.Model):
    LICENCE_CHOICES = [
        ("ALL", "Toutes les Licences (Tout le campus)"),
        ("L1", "Licence 1 (L1)"),
        ("L2", "Licence 2 (L2)"),
        ("L3", "Licence 3 (L3)"),
    ]
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="announcements", null=True, blank=True
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    licence = models.CharField(
        max_length=10,
        choices=LICENCE_CHOICES,
        default="ALL",
        blank=True,
        verbose_name="Licence concernée",
        help_text="Choisissez la Licence concernée par cette information (ou Toutes les Licences pour tout le campus)."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_global = models.BooleanField(default=False)  # annonce visible par tous

    def __str__(self):
        return f"{self.title} ({self.get_licence_display()})"