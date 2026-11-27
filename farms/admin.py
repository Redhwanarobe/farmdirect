"""Admin panel settings for farms and products."""

from django.contrib import admin

from .models import Farm, Product


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    """Show farms with their owner and area."""

    list_display = ("name", "owner", "area", "is_active")
    list_filter = ("area", "is_active")
    search_fields = ("name", "area")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Show products with price and stock, and allow quick edits."""

    list_display = ("name", "farm", "category", "price", "unit", "stock", "is_active")
    list_filter = ("category", "unit", "is_active")
    search_fields = ("name", "farm__name")
    list_editable = ("price", "stock", "is_active")
