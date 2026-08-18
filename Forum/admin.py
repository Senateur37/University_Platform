from django.contrib import admin
from .models import ForumCategory, ForumTopic, ForumPost

@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(ForumTopic)
class ForumTopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'course', 'author', 'created_at', 'is_pinned', 'is_closed', 'views_count')
    list_filter = ('category', 'is_pinned', 'is_closed', 'created_at')
    search_fields = ('title', 'content')

@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ('topic', 'author', 'created_at')
    search_fields = ('content',)
