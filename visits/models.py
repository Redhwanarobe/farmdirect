"""Farm visit slots and the bookings customers make."""

import secrets

from django.conf import settings
from django.db import models

from farms.models import Farm


class VisitSlot(models.Model):
    """One date and time when visitors can come to a farm."""

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="visit_slots")
    starts_at = models.DateTimeField()
    price_per_person = models.DecimalField(max_digits=8, decimal_places=2)
    capacity = models.PositiveIntegerField()
    is_cancelled = models.BooleanField(default=False)

    class Meta:
        ordering = ["starts_at"]

    def __str__(self):
        return f"{self.farm} - {self.starts_at:%d %b %Y %H:%M}"

    @property
    def spots_booked(self):
        """Count people in confirmed bookings."""
        confirmed = self.bookings.filter(status=Booking.Status.CONFIRMED)
        total = confirmed.aggregate(models.Sum("people"))["people__sum"]
        return total or 0

    @property
    def spots_left(self):
        """Return how many more people can still book."""
        return max(self.capacity - self.spots_booked, 0)

    @property
    def is_sold_out(self):
        """Return True when no spot is left."""
        return self.spots_left == 0


def make_booking_code():
    """Return a short random code like FD-3A9C1E."""
    return "FD-" + secrets.token_hex(3).upper()


class Booking(models.Model):
    """A customer's booking for one visit slot."""

    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    slot = models.ForeignKey(
        VisitSlot, on_delete=models.CASCADE, related_name="bookings"
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="visit_bookings",
    )
    people = models.PositiveIntegerField(default=1)
    code = models.CharField(max_length=12, unique=True, default=make_booking_code)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.CONFIRMED
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.customer}"

    @property
    def total_price(self):
        """Price for everyone in this booking."""
        return self.slot.price_per_person * self.people
