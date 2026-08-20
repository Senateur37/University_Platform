# courses/models.py
from django.db import models
from django.conf import settings

class Course(models.Model):
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)  # ex: INFO101
    category = models.CharField(max_length=100, default="Informatique", blank=True, verbose_name="Filière / Catégorie")
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="taught_courses",
        limit_choices_to={"user_type": "teacher"},
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="enrolled_courses",
        limit_choices_to={"user_type": "student"},
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} – {self.title}"

from Codex.validators import validate_secure_file_extension, validate_file_size

class CourseResource(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="resources")
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="courses/resources/", validators=[validate_secure_file_extension, validate_file_size])
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)