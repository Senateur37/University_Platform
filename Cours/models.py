# courses/models.py
from django.db import models
from django.conf import settings

class Course(models.Model):
    LICENCE_CHOICES = [
        ("ALL", "Toutes les Licences"),
        ("L1", "Licence 1 (L1)"),
        ("L2", "Licence 2 (L2)"),
        ("L3", "Licence 3 (L3)"),
    ]
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)  # ex: INFO101
    category = models.CharField(max_length=100, default="Informatique", blank=True, verbose_name="Filière / Catégorie")
    licence = models.CharField(max_length=10, choices=LICENCE_CHOICES, default="ALL", blank=True, verbose_name="Niveau / Licence requis")
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

    def user_has_access(self, user):
        """
        Vérifie si l'utilisateur a le niveau d'accès complet au cours (inscription, documents, devoirs).
        - Les enseignants et administrateurs accèdent à tout.
        - Un étudiant a accès si le cours est ouvert à 'ALL' ou correspond à sa Licence.
        """
        if not user or not user.is_authenticated:
            return False
        if user.is_teacher_or_admin:
            return True
        if user.user_type == 'student':
            if not self.licence or self.licence == 'ALL':
                return True
            return user.licence == self.licence
        return True

    def __str__(self):
        return f"{self.code} – {self.title}"

from Codex.validators import validate_secure_file_extension, validate_file_size

class CourseResource(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="resources")
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="courses/resources/", validators=[validate_secure_file_extension, validate_file_size])
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)