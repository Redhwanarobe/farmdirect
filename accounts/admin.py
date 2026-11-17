"""Admin panel settings for FarmDirect user accounts."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class FarmDirectUserAdmin(UserAdmin):
    """Show phone and role for each user in the admin panel."""

    list_display = ("username", "phone", "role", "is_staff")
    list_filter = ("role", "is_staff")
    fieldsets = UserAdmin.fieldsets + (("FarmDirect", {"fields": ("phone", "role")}),)
