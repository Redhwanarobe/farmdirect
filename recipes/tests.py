from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class RecipesViewsTestCase(TestCase):
    """Tests for recipe views."""

    def setUp(self):
        """Create and log in a test user."""
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        self.client.login(username="testuser", password="password123")

    def test_recipe_box_view(self):
        """Verify the recipe box view returns HTTP 200."""
        response = self.client.get(reverse("recipes:recipe_box"))
        self.assertEqual(response.status_code, 200)

    def test_allergy_preferences_view(self):
        """Verify the allergy preferences view returns HTTP 200."""
        response = self.client.get(reverse("recipes:allergy_preferences"))
        self.assertEqual(response.status_code, 200)

    def test_manage_subscription_view(self):
        """Verify the manage subscription view returns HTTP 200."""
        response = self.client.get(reverse("recipes:manage_subscription"))
        self.assertEqual(response.status_code, 200)

    def test_pantry_recipes_view(self):
        """Verify the pantry recipes view returns HTTP 200."""
        response = self.client.get(reverse("recipes:pantry_recipes"))
        self.assertEqual(response.status_code, 200)
