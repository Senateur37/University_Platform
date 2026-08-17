# announcements/models.py
from django.db import models
from django.conf import settings
from Cours.models import Course

class Announcement(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="announcements", null=True, blank=True
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_global = models.BooleanField(default=False)  # annonce visible par tous