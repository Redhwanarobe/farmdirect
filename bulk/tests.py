"""Tests for restaurant credit and bulk orders."""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from farms.tests import PASSWORD, make_farm, make_product

from .models import BulkOrder, CreditAccount
from .services import (
    BulkError,
    bulk_price,
    mark_paid,
    place_bulk_order,
    request_credit,
)


def make_restaurant(status=CreditAccount.Status.APPROVED):
    """Create a restaurant user with a credit account."""
    user = User.objects.create_user(
        username="dhakakitchen", password=PASSWORD, role="restaurant"
    )
    if status:
        CreditAccount.objects.create(
            restaurant=user,
            business_name="Dhaka Kitchen",
            trade_license="TL-1",
            status=status,
        )
    return user


class BulkPriceTests(TestCase):
    """Check the 10% bulk discount."""

    def test_ten_percent_off(self):
        """Normal case: Tk 80 becomes Tk 72.00."""
        self.assertEqual(bulk_price(Decimal("80")), Decimal("72.00"))

    def test_rounding_to_two_places(self):
        """Boundary case: Tk 33.33 becomes Tk 30.00 after rounding."""
        self.assertEqual(bulk_price(Decimal("33.33")), Decimal("30.00"))


class PlaceBulkOrderTests(TestCase):
    """Check the bulk order rules in services.py."""

    def setUp(self):
        """Create a product with 50 kg in stock."""
        _, farm = make_farm()
        self.product = make_product(farm, stock="50", price="80")

    def test_order_with_approved_credit(self):
        """Normal case: 10 kg at Tk 72 = Tk 720.00 and stock goes down."""
        user = make_restaurant()
        order = place_bulk_order(user, self.product.pk, Decimal("10"))
        self.product.refresh_from_db()
        self.assertEqual(order.total, Decimal("720.00"))
        self.assertEqual(self.product.stock, Decimal("40"))

    def test_total_has_two_decimals(self):
        """Bug B3 regression: 11 x 72 shows 792.00, not 792.0000."""
        order = place_bulk_order(make_restaurant(), self.product.pk, Decimal("11"))
        self.assertEqual(str(order.total), "792.00")

    def test_less_than_ten_is_rejected(self):
        """Boundary case: 9.99 units is below the minimum."""
        with self.assertRaisesMessage(BulkError, "at least 10"):
            place_bulk_order(make_restaurant(), self.product.pk, Decimal("9.99"))

    def test_no_credit_account(self):
        """Exception: a restaurant without credit cannot order."""
        user = make_restaurant(status=None)
        with self.assertRaisesMessage(BulkError, "not approved"):
            place_bulk_order(user, self.product.pk, Decimal("10"))

    def test_pending_credit(self):
        """Exception: pending credit is not enough to order."""
        user = make_restaurant(status=CreditAccount.Status.PENDING)
        with self.assertRaises(BulkError):
            place_bulk_order(user, self.product.pk, Decimal("10"))

    def test_not_enough_stock(self):
        """Invalid input: more than the stock is refused and stock stays."""
        with self.assertRaisesMessage(BulkError, "Not enough stock"):
            place_bulk_order(make_restaurant(), self.product.pk, Decimal("60"))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, Decimal("50"))


class InvoiceTests(TestCase):
    """Check due dates, overdue invoices and payment."""

    def setUp(self):
        """Create one placed order."""
        _, farm = make_farm()
        product = make_product(farm)
        self.user = make_restaurant()
        self.order = place_bulk_order(self.user, product.pk, Decimal("10"))

    def test_no_due_date_before_delivery(self):
        """Normal case: no due date until the order is delivered."""
        self.assertIsNone(self.order.due_date)

    def test_due_date_is_thirty_days_after_delivery(self):
        """Normal case: due date = delivery + 30 days."""
        now = timezone.now()
        self.order.delivered_at = now
        self.assertEqual(self.order.due_date, now + timedelta(days=30))

    def test_overdue_after_thirty_days(self):
        """Boundary case: 31 days after delivery and unpaid is overdue."""
        self.order.status = BulkOrder.Status.DELIVERED
        self.order.delivered_at = timezone.now() - timedelta(days=31)
        self.assertTrue(self.order.is_overdue)

    def test_cannot_pay_before_delivery(self):
        """Exception: a placed (not delivered) order cannot be paid."""
        with self.assertRaises(BulkError):
            mark_paid(self.order, self.user)

    def test_pay_delivered_invoice(self):
        """Normal case: a delivered invoice can be marked as paid."""
        self.order.status = BulkOrder.Status.DELIVERED
        self.order.delivered_at = timezone.now()
        mark_paid(self.order, self.user)
        self.assertEqual(self.order.status, BulkOrder.Status.PAID)


class CreditAndViewTests(TestCase):
    """Check credit requests and page access."""

    def test_second_credit_request_is_refused(self):
        """Invalid input: a restaurant can ask for credit only once."""
        user = make_restaurant(status=None)
        request_credit(user, "Dhaka Kitchen", "TL-1")
        user.refresh_from_db()
        with self.assertRaises(BulkError):
            request_credit(user, "Dhaka Kitchen", "TL-1")

    def test_customer_cannot_open_dashboard(self):
        """Security: only restaurants can open the bulk dashboard."""
        customer = User.objects.create_user(
            username="mizi", password=PASSWORD, role="customer"
        )
        self.client.force_login(customer)
        response = self.client.get(reverse("bulk:dashboard"))
        self.assertEqual(response.status_code, 403)
