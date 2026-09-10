from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Account extras', {'fields': ('role', 'phone_number', 'profile_picture', 'two_factor_enabled')}),
    )
