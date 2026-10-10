# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

from Codex.validators import validate_avatar_image, validate_file_size

class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ("student", "Étudiant"),
        ("teacher", "Enseignant"),
        ("admin", "Administrateur"),
    ]
    LICENCE_CHOICES = [
        ("L1", "Licence 1 (L1)"),
        ("L2", "Licence 2 (L2)"),
        ("L3", "Licence 3 (L3)"),
    ]
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    is_validated = models.BooleanField(default=True)  # validation manuelle ou automatique
    licence = models.CharField(max_length=10, choices=LICENCE_CHOICES, blank=True, null=True, verbose_name="Niveau / Licence")
    bio = models.TextField(blank=True, verbose_name="Biographie")
    filiere = models.CharField(max_length=100, blank=True, verbose_name="Filière / Département")
    avatar = models.FileField(upload_to="avatars/", null=True, blank=True, validators=[validate_avatar_image, validate_file_size])
    avatar_base64 = models.TextField(blank=True, null=True, verbose_name="Avatar permanent (Base64)")

    @property
    def avatar_url(self):
        """
        Retourne l'URL de l'avatar valide.
        1. Tente d'utiliser le fichier physique sur le disque s'il existe.
        2. Si le fichier physique a été effacé par un redémarrage Docker sans volume,
           utilise automatiquement la copie permanente Base64 stockée en base de données.
        3. Retourne None si aucun avatar n'est disponible.
        """
        if self.avatar:
            try:
                if self.avatar.storage.exists(self.avatar.name):
                    return self.avatar.url
            except Exception:
                pass
        if self.avatar_base64:
            return self.avatar_base64
        return None

    @property
    def is_teacher_or_admin(self):
        if not self.is_authenticated:
            return False
        return self.is_superuser or self.is_staff or self.user_type in ['teacher', 'admin']

    def save(self, *args, **kwargs):
        if (self.is_superuser or self.is_staff) and not self.user_type:
            self.user_type = 'admin'

        # Sauvegarde permanente de l'avatar en Base64 dans la BDD
        # pour éviter la perte lors des redémarrages de conteneurs Docker
        if self.avatar:
            try:
                import base64
                from io import BytesIO
                from PIL import Image

                if hasattr(self.avatar, 'file'):
                    self.avatar.seek(0)
                    img = Image.open(self.avatar)
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    img.thumbnail((256, 256), Image.Resampling.LANCZOS)
                    buf = BytesIO()
                    img.save(buf, format='JPEG', quality=85, optimize=True)
                    b64_str = base64.b64encode(buf.getvalue()).decode('utf-8')
                    self.avatar_base64 = f"data:image/jpeg;base64,{b64_str}"
                    self.avatar.seek(0)
                elif not self.avatar_base64:
                    try:
                        if self.avatar.storage.exists(self.avatar.name):
                            with self.avatar.storage.open(self.avatar.name, 'rb') as f:
                                img = Image.open(f)
                                if img.mode in ('RGBA', 'P'):
                                    img = img.convert('RGB')
                                img.thumbnail((256, 256), Image.Resampling.LANCZOS)
                                buf = BytesIO()
                                img.save(buf, format='JPEG', quality=85, optimize=True)
                                b64_str = base64.b64encode(buf.getvalue()).decode('utf-8')
                                self.avatar_base64 = f"data:image/jpeg;base64,{b64_str}"
                    except Exception:
                        pass
            except Exception:
                pass
        else:
            self.avatar_base64 = None

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