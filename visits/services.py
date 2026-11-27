"""Business rules for farm visits."""

from django.db import transaction
from django.utils import timezone

from .models import Booking, VisitSlot

SLOT_CANCELLED = "This visit was cancelled by the farm."
SLOT_PAST = "This visit has already started - please choose a later date."
SLOT_SOLD_OUT = "Sold Out - please choose another date."


class BookingError(Exception):
    """A booking problem whose message is shown to the customer."""


def send_sms(user, text):
    """Pretend to send an SMS by printing it in the terminal."""
    print(f"[FarmDirect SMS] To {user.phone or user.email}: {text}")


def book_visit(slot_id, customer, people):
    """Book spots safely, so two people can never take the same last spot."""
    with transaction.atomic():
        slot = VisitSlot.objects.select_for_update().get(pk=slot_id)
        if slot.is_cancelled:
            raise BookingError(SLOT_CANCELLED)
        if slot.starts_at <= timezone.now():
            raise BookingError(SLOT_PAST)
        if slot.is_sold_out:
            raise BookingError(SLOT_SOLD_OUT)
        if people > slot.spots_left:
            raise BookingError(
                f"Only {slot.spots_left} spots left - please book fewer people."
            )
        booking = Booking.objects.create(slot=slot, customer=customer, people=people)
    send_sms(customer, f"Your farm visit is booked. Your code is {booking.code}.")
    return booking


def cancel_slot(slot):
    """Cancel a slot (for example for bad weather) and tell every visitor."""
    with transaction.atomic():
        slot.is_cancelled = True
        slot.save(update_fields=["is_cancelled"])
        confirmed = slot.bookings.filter(status=Booking.Status.CONFIRMED)
        bookings = list(confirmed.select_related("customer"))
        confirmed.update(status=Booking.Status.CANCELLED)
    for booking in bookings:
        send_sms(
            booking.customer,
            f"Your visit {booking.code} was cancelled by the farm. "
            f"Your refund of Tk {booking.total_price} will be sent.",
        )
    return len(bookings)
