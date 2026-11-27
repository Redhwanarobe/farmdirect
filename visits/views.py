"""Pages for booking farm visits and managing visit slots."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from farms.services import get_own_farm

from .forms import BookingForm, VisitSlotForm
from .models import VisitSlot
from .services import BookingError, book_visit, cancel_slot

MY_BOOKINGS = "visits:my_bookings"
FARMER_SLOTS = "visits:farmer_slots"


def slot_list(request):
    """Show upcoming visits on all active farms."""
    slots = VisitSlot.objects.filter(
        starts_at__gt=timezone.now(), is_cancelled=False, farm__is_active=True
    ).select_related("farm")
    return render(request, "visits/slot_list.html", {"slots": slots})


@login_required
def book(request, pk):
    """Let a customer book spots on one visit."""
    if request.user.role != "customer":
        raise PermissionDenied("Only customers can book farm visits.")
    slot = get_object_or_404(VisitSlot, pk=pk)
    form = BookingForm(request.POST or None)
    if form.is_valid():
        try:
            booking = book_visit(slot.pk, request.user, form.cleaned_data["people"])
        except BookingError as error:
            form.add_error("people", str(error))
        else:
            messages.success(request, f"Booked! Your code is {booking.code}.")
            return redirect(MY_BOOKINGS)
    return render(request, "visits/book.html", {"slot": slot, "form": form})


@login_required
def my_bookings(request):
    """Show the customer's own bookings, newest first."""
    bookings = request.user.visit_bookings.select_related("slot__farm").order_by(
        "-created_at"
    )
    return render(request, "visits/my_bookings.html", {"bookings": bookings})


@login_required
def farmer_slots(request):
    """Show the farmer's own visit slots."""
    farm = get_own_farm(request.user)
    slots = farm.visit_slots.order_by("-starts_at")
    return render(request, "visits/farmer_slots.html", {"farm": farm, "slots": slots})


@login_required
def slot_add(request):
    """Let a farmer add a new visit slot to their farm."""
    farm = get_own_farm(request.user)
    form = VisitSlotForm(request.POST or None)
    if form.is_valid():
        slot = form.save(commit=False)
        slot.farm = farm
        slot.save()
        messages.success(request, "Visit slot added.")
        return redirect(FARMER_SLOTS)
    return render(request, "visits/slot_form.html", {"form": form})


@login_required
@require_POST
def slot_cancel(request, pk):
    """Cancel a slot, for example for bad weather."""
    farm = get_own_farm(request.user)
    slot = get_object_or_404(VisitSlot, pk=pk, farm=farm, is_cancelled=False)
    count = cancel_slot(slot)
    messages.info(
        request, f"Visit cancelled. {count} bookings were told about their refund."
    )
    return redirect(FARMER_SLOTS)
