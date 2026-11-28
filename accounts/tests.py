"""Tests for phone numbers and the page after login."""

from django.test import TestCase

from farms.tests import PASSWORD, make_farm

from .models import User
from .services import home_url_for, normalize_bd_phone


class NormalizePhoneTests(TestCase):
    """Check Bangladeshi phone numbers."""

    def test_local_number(self):
        """Normal case: 01712345678 becomes +8801712345678."""
        self.assertEqual(normalize_bd_phone("01712345678"), "+8801712345678")

    def test_number_with_dashes(self):
        """Boundary case: dashes are removed."""
        self.assertEqual(normalize_bd_phone("017-1234-5678"), "+8801712345678")

    def test_wrong_operator(self):
        """Invalid input: 012 is not a Bangladeshi mobile operator."""
        self.assertIsNone(normalize_bd_phone("01212345678"))


class HomeUrlTests(TestCase):
    """Check where each role goes after login."""

    def make(self, username, role, **extra):
        """Create a user with a role."""
        return User.objects.create_user(
            username=username, password=PASSWORD, role=role, **extra
        )

    def test_staff_goes_to_admin(self):
        """Staff users go to the admin panel."""
        staff = self.make("boss", "customer", is_staff=True)
        self.assertEqual(home_url_for(staff), "admin:index")

    def test_farmer_with_farm_goes_to_dashboard(self):
        """A farmer with a farm goes to the farm dashboard."""
        owner, _ = make_farm()
        self.assertEqual(home_url_for(owner), "farms:dashboard")

    def test_farmer_without_farm_goes_home(self):
        """Boundary case: a new farmer with no farm goes home, not 403."""
        farmer = self.make("newfarmer", "farmer")
        self.assertEqual(home_url_for(farmer), "core:home")

    def test_restaurant_goes_to_bulk(self):
        """A restaurant goes to the bulk orders dashboard."""
        restaurant = self.make("kitchen", "restaurant")
        self.assertEqual(home_url_for(restaurant), "bulk:dashboard")

    def test_customer_goes_home(self):
        """A customer goes to the home page."""
        self.assertEqual(home_url_for(self.make("mizi", "customer")), "core:home")
