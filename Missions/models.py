# assignments/models.py
from django.db import models
from django.conf import settings
from Cours.models import Course

from Codex.validators import validate_secure_file_extension, validate_file_size

class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=200)
    description = models.TextField()
    max_points = models.DecimalField(max_digits=5, decimal_places=2, default=20.00, verbose_name="Note maximale")
    attachment = models.FileField(upload_to="assignments/attachments/", null=True, blank=True, verbose_name="Sujet / Pièce jointe", validators=[validate_secure_file_extension, validate_file_size])
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course.code} – {self.title}"

class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"user_type": "student"},
    )
    file = models.FileField(upload_to="assignments/submissions/", validators=[validate_secure_file_extension, validate_file_size])
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)

    class Meta:
        unique_together = ("assignment", "student")