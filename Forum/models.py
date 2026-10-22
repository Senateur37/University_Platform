from django.db import models
from django.conf import settings
from Cours.models import Course

class ForumCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=30, default="💬")

    class Meta:
        verbose_name = "Catégorie du forum"
        verbose_name_plural = "Catégories du forum"
        ordering = ['name']

    def __str__(self):
        return self.name


class ForumTopic(models.Model):
    LICENCE_CHOICES = [
        ("ALL", "Forum Général (Tout le campus)"),
        ("L1", "Forum Licence 1 (L1)"),
        ("L2", "Forum Licence 2 (L2)"),
        ("L3", "Forum Licence 3 (L3)"),
    ]
    title = models.CharField(max_length=200)
    licence = models.CharField(
        max_length=10,
        choices=LICENCE_CHOICES,
        default="ALL",
        blank=True,
        verbose_name="Espace Licence du Forum",
        help_text="Choisissez si cette discussion appartient au forum privé d'une Licence (L1, L2, L3) ou au Forum Général."
    )
    category = models.ForeignKey(ForumCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="topics")
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name="forum_topics")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="forum_topics")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def user_has_access(self, user):
        """Vérifie si l'utilisateur a le droit d'accéder à ce sujet selon sa Licence."""
        if not user or not user.is_authenticated:
            return self.licence in ['ALL', '', None]
        if user.is_teacher_or_admin:
            return True
        if user.user_type == 'student':
            if self.licence and self.licence != 'ALL':
                return user.licence == self.licence
            return True
        return True

    def __str__(self):
        return f"[{self.get_licence_display()}] {self.title}"


class ForumPost(models.Model):
    topic = models.ForeignKey(ForumTopic, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="forum_posts")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Réponse de {self.author.username} sur {self.topic.title}"
