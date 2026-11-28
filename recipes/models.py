from decimal import Decimal

from django.conf import settings
from django.db import models


class Ingredient(models.Model):
    """Ingredient item used in recipe boxes, allergy filtering, and pantry matching."""

    ALLERGEN_CHOICES = [
        ("none", "None"),
        ("nuts", "Nuts"),
        ("gluten", "Gluten"),
        ("dairy", "Dairy"),
        ("eggs", "Eggs"),
        ("soy", "Soy"),
        ("shellfish", "Shellfish"),
    ]
    name = models.CharField(max_length=100, unique=True)
    allergen_tag = models.CharField(
        max_length=20, choices=ALLERGEN_CHOICES, default="none"
    )
    estimated_price_bdt = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0.00")
    )

    def __str__(self):
        return f"{self.name} ({self.get_allergen_tag_display()})"


class Recipe(models.Model):
    """Recipe available for weekly recipe boxes and pantry recommendations."""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    instructions = models.TextField()
    servings_base = models.PositiveIntegerField(default=1)
    has_unconfirmed_ingredients = models.BooleanField(
        default=False,
        help_text=(
            "Exclude from recommendations when ingredients are unconfirmed "
            "or conflicting."
        ),
    )
    ingredients = models.ManyToManyField(Ingredient, through="RecipeIngredient")

    def __str__(self):
        return self.title


class RecipeIngredient(models.Model):
    """Per-serving ingredient quantity required by a recipe."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity_per_serving = models.DecimalField(max_digits=6, decimal_places=2)
    unit = models.CharField(max_length=20, default="g")

    def __str__(self):
        return f"{self.quantity_per_serving} {self.unit} {self.ingredient.name}"


class UserAllergyPreference(models.Model):
    """Blocked allergens and blocked ingredients for a user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="allergy_preference",
    )
    blocked_allergens = models.JSONField(default=list)
    blocked_ingredients = models.ManyToManyField(Ingredient, blank=True)

    def __str__(self):
        return f"Allergies for {self.user}"


class RecipeSubscription(models.Model):
    """User subscription for 1-day, 3-day, or weekly recipe boxes."""

    PLAN_CHOICES = [
        ("daily", "1-Day"),
        ("three_day", "3-Day"),
        ("weekly", "Weekly"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("paused", "Paused"),
        ("cancelled", "Cancelled"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES, default="weekly")
    delivery_day = models.CharField(max_length=20, default="Friday")
    servings = models.PositiveIntegerField(default=2)
    budget_bdt = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    selected_recipes = models.ManyToManyField(Recipe)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.get_plan_type_display()} ({self.status})"


class DeliverySlot(models.Model):
    """Scheduled delivery occurrence that can be skipped or locked for packing."""

    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("skipped", "Skipped"),
        ("locked", "Locked for Packing"),
        ("delivered", "Delivered"),
    ]
    subscription = models.ForeignKey(
        RecipeSubscription, on_delete=models.CASCADE, related_name="delivery_slots"
    )
    delivery_date = models.DateField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="scheduled"
    )
    locked_for_packing = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.delivery_date} ({self.status})"


class PantryItem(models.Model):
    """Ingredient kept at home in a user's pantry."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pantry_items"
    )
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity_label = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = ("user", "ingredient")

    def __str__(self):
        return f"{self.ingredient.name} ({self.user})"
