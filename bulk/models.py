"""Credit accounts and bulk orders for restaurants."""

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from farms.models import Product

CREDIT_DAYS = 30


class CreditAccount(models.Model):
    """A restaurant's request to buy now and pay within 30 days."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    restaurant = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="credit_account",
        limit_choices_to={"role": "restaurant"},
    )
    business_name = models.CharField(max_length=120)
    trade_license = models.CharField(max_length=60)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.business_name} ({self.get_status_display()})"

    @property
    def is_approved(self):
        """Return True if the admin approved this credit account."""
        return self.status == self.Status.APPROVED


class BulkOrder(models.Model):
    """A large order on credit, which becomes an invoice after delivery."""

    class Status(models.TextChoices):
        PLACED = "placed", "Placed"
        DELIVERED = "delivered", "Delivered (invoice sent)"
        PAID = "paid", "Paid"

    restaurant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bulk_orders",
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="bulk_orders"
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PLACED
    )
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.pk} {self.product.name} x {self.quantity}"

    @property
    def total(self):
        """Total price in Taka."""
        return (self.unit_price * self.quantity).quantize(Decimal("0.01"))

    @property
    def due_date(self):
        """Payment is due 30 days after delivery."""
        if self.delivered_at is None:
            return None
        return self.delivered_at + timedelta(days=CREDIT_DAYS)

    @property
    def is_overdue(self):
        """Return True if the invoice is late and still unpaid."""
        return (
            self.status == self.Status.DELIVERED
            and self.due_date is not None
            and timezone.now() > self.due_date
        )
