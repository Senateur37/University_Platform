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
    title = models.CharField(max_length=200)
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

    def __str__(self):
        return self.title


class ForumPost(models.Model):
    topic = models.ForeignKey(ForumTopic, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="forum_posts")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Réponse de {self.author.username} sur {self.topic.title}"
