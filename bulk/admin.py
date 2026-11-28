"""Admin tools for restaurant credit and bulk orders."""

from django.contrib import admin, messages
from django.utils import timezone

from .models import BulkOrder, CreditAccount


@admin.register(CreditAccount)
class CreditAccountAdmin(admin.ModelAdmin):
    """Let the admin approve or reject credit requests."""

    list_display = (
        "business_name",
        "restaurant",
        "trade_license",
        "status",
        "requested_at",
    )
    list_filter = ("status",)
    search_fields = ("business_name", "trade_license")
    actions = ["approve_credit", "reject_credit"]

    @admin.action(description="Approve selected credit requests")
    def approve_credit(self, request, queryset):
        """Give 30-day credit to the selected restaurants."""
        count = queryset.update(status=CreditAccount.Status.APPROVED)
        self.message_user(
            request, f"{count} credit request(s) approved.", messages.SUCCESS
        )

    @admin.action(description="Reject selected credit requests")
    def reject_credit(self, request, queryset):
        """Refuse credit to the selected restaurants."""
        count = queryset.update(status=CreditAccount.Status.REJECTED)
        self.message_user(
            request, f"{count} credit request(s) rejected.", messages.WARNING
        )


@admin.register(BulkOrder)
class BulkOrderAdmin(admin.ModelAdmin):
    """Show bulk orders and let the admin mark them as delivered."""

    list_display = (
        "id",
        "restaurant",
        "product",
        "quantity",
        "unit_price",
        "status",
        "due_date",
    )
    list_filter = ("status",)
    actions = ["mark_delivered"]

    @admin.action(
        description="Mark selected orders as delivered (start 30-day invoice)"
    )
    def mark_delivered(self, request, queryset):
        """Set the delivery time so the 30-day payment period starts."""
        placed = queryset.filter(status=BulkOrder.Status.PLACED)
        count = placed.update(
            status=BulkOrder.Status.DELIVERED, delivered_at=timezone.now()
        )
        self.message_user(
            request, f"{count} order(s) marked as delivered.", messages.SUCCESS
        )
