"""Tests for farm visit booking."""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from farms.tests import PASSWORD, make_farm

from .forms import VisitSlotForm
from .models import Booking, VisitSlot
from .services import (
    SLOT_CANCELLED,
    SLOT_PAST,
    SLOT_SOLD_OUT,
    BookingError,
    book_visit,
    cancel_slot,
)


def make_slot(farm, capacity=3, days=7):
    """Create a visit slot some days from now."""
    return VisitSlot.objects.create(
        farm=farm,
        starts_at=timezone.now() + timedelta(days=days),
        price_per_person=Decimal("100"),
        capacity=capacity,
    )


class BookVisitTests(TestCase):
    """Check the booking rules in services.py."""

    def setUp(self):
        """Create a farm, a slot with 3 spots and a customer."""
        _, self.farm = make_farm()
        self.slot = make_slot(self.farm, capacity=3)
        self.customer = User.objects.create_user(
            username="mizi", password=PASSWORD, role="customer"
        )

    def test_booking_reduces_spots(self):
        """Normal case: booking 2 people leaves 1 spot and gives a code."""
        booking = book_visit(self.slot.pk, self.customer, 2)
        self.assertEqual(self.slot.spots_left, 1)
        self.assertTrue(booking.code.startswith("FD-"))
        self.assertEqual(booking.total_price, Decimal("200"))

    def test_booking_last_spots_makes_sold_out(self):
        """Boundary case: booking exactly all spots makes the slot sold out."""
        book_visit(self.slot.pk, self.customer, 3)
        self.assertTrue(self.slot.is_sold_out)

    def test_too_many_people(self):
        """Invalid input: more people than spots left is refused."""
        with self.assertRaisesMessage(BookingError, "Only 3 spots left"):
            book_visit(self.slot.pk, self.customer, 4)

    def test_sold_out_slot(self):
        """Exception: a sold out slot cannot be booked."""
        book_visit(self.slot.pk, self.customer, 3)
        with self.assertRaisesMessage(BookingError, SLOT_SOLD_OUT):
            book_visit(self.slot.pk, self.customer, 1)

    def test_past_slot(self):
        """Exception: a visit that already started cannot be booked."""
        old = make_slot(self.farm, days=-1)
        with self.assertRaisesMessage(BookingError, SLOT_PAST):
            book_visit(old.pk, self.customer, 1)

    def test_cancelled_slot(self):
        """Exception: a cancelled slot cannot be booked."""
        cancel_slot(self.slot)
        with self.assertRaisesMessage(BookingError, SLOT_CANCELLED):
            book_visit(self.slot.pk, self.customer, 1)


class CancelSlotTests(TestCase):
    """Check that the farmer can cancel a slot for bad weather."""

    def test_cancel_cancels_all_bookings(self):
        """Normal case: every booking is cancelled and spots come back."""
        _, farm = make_farm()
        slot = make_slot(farm, capacity=3)
        customer = User.objects.create_user(
            username="mizi", password=PASSWORD, role="customer"
        )
        book_visit(slot.pk, customer, 2)
        book_visit(slot.pk, customer, 1)
        self.assertEqual(cancel_slot(slot), 2)
        statuses = set(slot.bookings.values_list("status", flat=True))
        self.assertEqual(statuses, {Booking.Status.CANCELLED})
        self.assertEqual(slot.spots_left, 3)


class VisitSlotFormTests(TestCase):
    """Check the farmer's slot form."""

    def data(self, days=7, price="100", capacity="3"):
        """Return form data for a slot some days from now."""
        start = timezone.localtime() + timedelta(days=days)
        return {
            "starts_at": start.strftime("%Y-%m-%d %H:%M"),
            "price_per_person": price,
            "capacity": capacity,
        }

    def test_future_slot_is_valid(self):
        """Normal case: a future date is accepted."""
        self.assertTrue(VisitSlotForm(self.data()).is_valid())

    def test_past_date_is_rejected(self):
        """Invalid input: a past date is refused."""
        self.assertFalse(VisitSlotForm(self.data(days=-1)).is_valid())

    def test_price_zero_is_rejected(self):
        """Boundary case: price 0 is refused."""
        self.assertFalse(VisitSlotForm(self.data(price="0")).is_valid())


class BookViewTests(TestCase):
    """Check who can open the booking page."""

    def test_farmer_cannot_book(self):
        """Security: only customers can book, others get 403."""
        owner, farm = make_farm()
        slot = make_slot(farm)
        self.client.force_login(owner)
        response = self.client.get(reverse("visits:book", args=[slot.pk]))
        self.assertEqual(response.status_code, 403)
