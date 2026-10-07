from django.contrib import admin
from .models import Announcement

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'licence', 'course', 'author', 'is_global', 'created_at')
    list_filter = ('licence', 'is_global', 'created_at')
    search_fields = ('title', 'content', 'author__username')

