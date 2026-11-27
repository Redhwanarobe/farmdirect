"""Admin panel settings for farm visits."""

from django.contrib import admin

from .models import Booking, VisitSlot


@admin.register(VisitSlot)
class VisitSlotAdmin(admin.ModelAdmin):
    """Show visit slots with how many spots are left."""

    list_display = (
        "farm",
        "starts_at",
        "price_per_person",
        "capacity",
        "spots_left",
        "is_cancelled",
    )
    list_filter = ("farm", "is_cancelled")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Show bookings with their code and status."""

    list_display = ("code", "customer", "slot", "people", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("code", "customer__username")
