"""Restaurant dashboard for credit and bulk orders."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import BulkOrderForm, CreditRequestForm
from .models import BulkOrder
from .services import BulkError, mark_paid, place_bulk_order, request_credit

DASHBOARD = "bulk:dashboard"


def check_restaurant(user):
    """Only restaurant accounts can use bulk ordering."""
    if getattr(user, "role", None) != "restaurant":
        raise PermissionDenied("Only restaurant accounts can open this page.")


@login_required
def dashboard(request):
    """Show credit status, the order form and all invoices."""
    check_restaurant(request.user)
    context = {
        "account": getattr(request.user, "credit_account", None),
        "orders": request.user.bulk_orders.select_related("product__farm"),
        "credit_form": CreditRequestForm(),
        "order_form": BulkOrderForm(),
    }
    return render(request, "bulk/dashboard.html", context)


@login_required
@require_POST
def credit_request(request):
    """Send a credit request to the admin."""
    check_restaurant(request.user)
    form = CreditRequestForm(request.POST)
    if form.is_valid():
        try:
            request_credit(request.user, **form.cleaned_data)
        except BulkError as error:
            messages.error(request, str(error))
        else:
            messages.success(
                request, "Credit request sent. Please wait for admin approval."
            )
    else:
        messages.error(request, "Please fill in your business name and trade licence.")
    return redirect(DASHBOARD)


@login_required
@require_POST
def place_order(request):
    """Place a bulk order on credit."""
    check_restaurant(request.user)
    form = BulkOrderForm(request.POST)
    if not form.is_valid():
        messages.error(
            request, "Bulk orders need at least 10 units of an available product."
        )
        return redirect(DASHBOARD)
    try:
        order = place_bulk_order(
            request.user, form.cleaned_data["product"].pk, form.cleaned_data["quantity"]
        )
    except BulkError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, f"Order #{order.pk} placed. Total Tk {order.total}.")
    return redirect(DASHBOARD)


@login_required
@require_POST
def pay(request, pk):
    """Mark one of the restaurant's own invoices as paid (simulated)."""
    check_restaurant(request.user)
    order = get_object_or_404(BulkOrder, pk=pk, restaurant=request.user)
    try:
        mark_paid(order, request.user)
    except BulkError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, f"Invoice #{order.pk} paid. Thank you!")
    return redirect(DASHBOARD)
