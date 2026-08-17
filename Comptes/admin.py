from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
	fieldsets = UserAdmin.fieldsets + (('Profil universitaire', {'fields': ('user_type', 'is_validated')}),)
	list_display = ('username', 'email', 'user_type', 'is_validated', 'is_staff')
