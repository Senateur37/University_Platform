# assignments/models.py
from django.db import models
from django.conf import settings
from Cours.models import Course

from Codex.validators import validate_secure_file_extension, validate_file_size

class Assignment(models.Model):
    LICENCE_CHOICES = [
        ("ALL", "Toutes les Licences"),
        ("L1", "Licence 1 (L1)"),
        ("L2", "Licence 2 (L2)"),
        ("L3", "Licence 3 (L3)"),
    ]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    licence = models.CharField(
        max_length=10,
        choices=LICENCE_CHOICES,
        default="ALL",
        blank=True,
        verbose_name="Licence ciblée",
        help_text="Choisissez la Licence concernée par cette mission (ou Toutes les Licences)."
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    max_points = models.DecimalField(max_digits=5, decimal_places=2, default=20.00, verbose_name="Note maximale")
    attachment = models.FileField(upload_to="assignments/attachments/", null=True, blank=True, verbose_name="Sujet / Pièce jointe", validators=[validate_secure_file_extension, validate_file_size])
    attachment_base64 = models.TextField(blank=True, null=True, verbose_name="Pièce jointe permanente (Base64)")
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.attachment:
            try:
                import base64
                if hasattr(self.attachment, 'file'):
                    self.attachment.seek(0)
                    data = self.attachment.read()
                    self.attachment_base64 = base64.b64encode(data).decode('utf-8')
                    self.attachment.seek(0)
                elif not self.attachment_base64:
                    if self.attachment.storage.exists(self.attachment.name):
                        with self.attachment.storage.open(self.attachment.name, 'rb') as f:
                            self.attachment_base64 = base64.b64encode(f.read()).decode('utf-8')
            except Exception:
                pass
        super().save(*args, **kwargs)

    def user_has_access(self, user):
        """Vérifie si un étudiant a accès à ce devoir en fonction de sa Licence."""
        if not user or not user.is_authenticated:
            return False
        if user.is_teacher_or_admin:
            return True
        if user.user_type == 'student':
            if self.licence and self.licence != 'ALL':
                return user.licence == self.licence
            return self.course.user_has_access(user)
        return True

    def __str__(self):
        return f"{self.course.code} – {self.title} ({self.get_licence_display()})"

    @property
    def safe_attachment_url(self):
        """Retourne l'URL de la pièce jointe sans lever de ValueError si aucun fichier n'est associé."""
        try:
            if self.attachment and hasattr(self.attachment, 'url') and self.attachment.name:
                return self.attachment.url
        except Exception:
            pass
        return None

class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"user_type": "student"},
    )
    file = models.FileField(upload_to="assignments/submissions/", validators=[validate_secure_file_extension, validate_file_size])
    file_base64 = models.TextField(blank=True, null=True, verbose_name="Copie permanente (Base64)")
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)

    @property
    def safe_file_url(self):
        """Retourne l'URL du fichier soumis sans lever de ValueError si aucun fichier n'est associé."""
        try:
            if self.file and hasattr(self.file, 'url') and self.file.name:
                return self.file.url
        except Exception:
            pass
        return None

    def save(self, *args, **kwargs):
        if self.file:
            try:
                import base64
                if hasattr(self.file, 'file'):
                    self.file.seek(0)
                    data = self.file.read()
                    self.file_base64 = base64.b64encode(data).decode('utf-8')
                    self.file.seek(0)
                elif not self.file_base64:
                    if self.file.storage.exists(self.file.name):
                        with self.file.storage.open(self.file.name, 'rb') as f:
                            self.file_base64 = base64.b64encode(f.read()).decode('utf-8')
            except Exception:
                pass
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ("assignment", "student")