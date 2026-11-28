"""Tests for farms: stock, product form and farmer access."""

from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .forms import ProductForm
from .models import Farm, Product
from .services import get_own_farm

PASSWORD = "pass12345678"


def make_farm(username="karim"):
    """Create a farmer and a farm for tests."""
    owner = User.objects.create_user(
        username=username, password=PASSWORD, role="farmer"
    )
    farm = Farm.objects.create(
        owner=owner,
        name=f"{username} farm",
        area="Savar",
        address="Savar, Dhaka",
        latitude=Decimal("23.79"),
        longitude=Decimal("90.26"),
    )
    return owner, farm


def make_product(farm, stock="50", price="80"):
    """Create a product for tests."""
    return Product.objects.create(
        farm=farm,
        name="Tomato",
        category="Vegetables",
        unit="kg",
        price=Decimal(price),
        stock=Decimal(stock),
    )


class ProductStockTests(TestCase):
    """Check the in_stock property."""

    def test_in_stock_when_stock_left(self):
        """Normal case: stock above zero means in stock."""
        _, farm = make_farm()
        self.assertTrue(make_product(farm, stock="5").in_stock)

    def test_out_of_stock_at_zero(self):
        """Boundary case: stock exactly zero means out of stock."""
        _, farm = make_farm()
        self.assertFalse(make_product(farm, stock="0").in_stock)


class ProductFormTests(TestCase):
    """Check the product form rules."""

    def data(self, **changes):
        """Return valid form data, with some fields changed."""
        values = {
            "name": "Potato",
            "category": "Vegetables",
            "unit": "kg",
            "price": "40",
            "stock": "30",
            "is_active": "on",
        }
        values.update(changes)
        return values

    def test_valid_product(self):
        """Normal case: correct data is accepted."""
        self.assertTrue(ProductForm(self.data()).is_valid())

    def test_price_zero_is_rejected(self):
        """Boundary case: price 0 is not allowed."""
        form = ProductForm(self.data(price="0"))
        self.assertFalse(form.is_valid())
        self.assertIn("Price must be more than 0 Taka.", form.errors["price"])

    def test_stock_zero_is_allowed(self):
        """Boundary case: stock 0 is allowed (shows Out of Stock)."""
        self.assertTrue(ProductForm(self.data(stock="0")).is_valid())

    def test_negative_stock_is_rejected(self):
        """Invalid input: stock cannot be negative."""
        form = ProductForm(self.data(stock="-1"))
        self.assertFalse(form.is_valid())
        self.assertIn("Stock cannot be negative.", form.errors["stock"])

    def test_missing_name_is_rejected(self):
        """Invalid input: name is required."""
        self.assertFalse(ProductForm(self.data(name="")).is_valid())


class GetOwnFarmTests(TestCase):
    """Check who can open farmer pages."""

    def test_farmer_gets_own_farm(self):
        """Normal case: a farmer gets their own farm."""
        owner, farm = make_farm()
        self.assertEqual(get_own_farm(owner), farm)

    def test_customer_is_blocked(self):
        """Exception: a customer cannot open farmer pages."""
        customer = User.objects.create_user(
            username="mizi", password=PASSWORD, role="customer"
        )
        with self.assertRaises(PermissionDenied):
            get_own_farm(customer)

    def test_farmer_without_farm_is_blocked(self):
        """Exception: a farmer with no active farm is blocked."""
        farmer = User.objects.create_user(
            username="newfarmer", password=PASSWORD, role="farmer"
        )
        with self.assertRaises(PermissionDenied):
            get_own_farm(farmer)


class FarmerDashboardViewTests(TestCase):
    """Check the farmer pages through the web client."""

    def test_login_required(self):
        """Exception: a visitor who is not logged in is sent to login."""
        response = self.client.get(reverse("farms:dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_farmer_sees_own_products(self):
        """Normal case: the farmer sees their products."""
        owner, farm = make_farm()
        make_product(farm)
        self.client.force_login(owner)
        response = self.client.get(reverse("farms:dashboard"))
        self.assertContains(response, "Tomato")

    def test_cannot_edit_other_farmers_product(self):
        """Security: editing another farm's product gives 404."""
        _, other_farm = make_farm("rahim")
        product = make_product(other_farm)
        owner, _ = make_farm("karim")
        self.client.force_login(owner)
        url = reverse("farms:product_edit", args=[product.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
