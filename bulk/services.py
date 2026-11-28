"""Business rules for restaurant credit and bulk orders."""

from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.utils import timezone

from farms.models import Product

from .models import BulkOrder, CreditAccount

BULK_MIN_QUANTITY = Decimal("10")
BULK_DISCOUNT = Decimal("0.10")


class BulkError(Exception):
    """A bulk order problem whose message is shown to the restaurant."""


def send_sms(user, text):
    """Pretend to send an SMS by printing it in the terminal."""
    print(f"[FarmDirect SMS] To {user.phone or user.email}: {text}")


def bulk_price(price):
    """Return the price per unit after the bulk discount."""
    return (price * (1 - BULK_DISCOUNT)).quantize(Decimal("0.01"), ROUND_HALF_UP)


def request_credit(user, business_name, trade_license):
    """Create a credit request that the admin must approve."""
    if hasattr(user, "credit_account"):
        raise BulkError("You have already requested credit.")
    return CreditAccount.objects.create(
        restaurant=user, business_name=business_name, trade_license=trade_license
    )


def place_bulk_order(user, product_id, quantity):
    """Place a bulk order on 30-day credit and reduce the farm's stock."""
    account = getattr(user, "credit_account", None)
    if account is None or not account.is_approved:
        raise BulkError("Your credit account is not approved yet.")
    if quantity < BULK_MIN_QUANTITY:
        raise BulkError("Bulk orders need at least 10 units.")
    with transaction.atomic():
        product = Product.objects.select_for_update().get(pk=product_id)
        if not product.is_active:
            raise BulkError("This product is not available.")
        if quantity > product.stock:
            raise BulkError(
                f"Not enough stock - only {product.stock} {product.unit} left."
            )
        product.stock -= quantity
        product.save(update_fields=["stock"])
        order = BulkOrder.objects.create(
            restaurant=user,
            product=product,
            quantity=quantity,
            unit_price=bulk_price(product.price),
        )
    send_sms(user, f"Bulk order #{order.pk} placed. Total Tk {order.total}.")
    send_sms(
        product.farm.owner,
        f"New bulk order #{order.pk}: {quantity} {product.unit} {product.name}.",
    )
    return order


def mark_paid(order, user):
    """Let the restaurant mark a delivered invoice as paid (simulated)."""
    if order.restaurant != user or order.status != BulkOrder.Status.DELIVERED:
        raise BulkError("Only a delivered invoice can be paid.")
    order.status = BulkOrder.Status.PAID
    order.paid_at = timezone.now()
    order.save(update_fields=["status", "paid_at"])
    return order
