"""Add demo ingredients and Bangladeshi recipes so Recipe Box can be tested."""

from decimal import Decimal

from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Recipe, RecipeIngredient

# name: (allergen tag, price in Taka per 100 g)
INGREDIENTS = {
    "Rice": ("none", "7.00"),
    "Red lentils": ("none", "12.00"),
    "Onion": ("none", "6.00"),
    "Potato": ("none", "4.00"),
    "Tomato": ("none", "8.00"),
    "Spinach": ("none", "8.00"),
    "Mustard oil": ("none", "18.00"),
    "Chicken": ("none", "30.00"),
    "Rui fish": ("none", "35.00"),
    "Shrimp": ("shellfish", "80.00"),
    "Milk": ("dairy", "10.00"),
    "Egg": ("eggs", "30.00"),
    "Wheat flour": ("gluten", "6.00"),
    "Peanuts": ("nuts", "25.00"),
}

# title: (description, [(ingredient, grams per person), ...])
RECIPES = {
    "Bhuna Khichuri": (
        "Rice and lentils cooked with onion. Easy rainy-day meal.",
        [("Rice", 75), ("Red lentils", 40), ("Onion", 30), ("Mustard oil", 10)],
    ),
    "Chicken Curry with Rice": (
        "Home-style chicken curry with potato, served with rice.",
        [
            ("Chicken", 150),
            ("Rice", 100),
            ("Onion", 40),
            ("Potato", 50),
            ("Mustard oil", 15),
        ],
    ),
    "Rui Fish Jhol": (
        "Light fish curry with potato and tomato.",
        [("Rui fish", 150), ("Potato", 60), ("Tomato", 40), ("Mustard oil", 15)],
    ),
    "Chingri Malai Curry": (
        "Shrimp cooked in milk. Contains shellfish and dairy.",
        [("Shrimp", 120), ("Milk", 80), ("Onion", 30), ("Mustard oil", 10)],
    ),
    "Egg Paratha": (
        "Flatbread with egg. Contains gluten and eggs.",
        [("Wheat flour", 100), ("Egg", 60), ("Onion", 20), ("Mustard oil", 15)],
    ),
    "Spinach Peanut Bhaji": (
        "Stir-fried spinach with crushed peanuts. Contains nuts.",
        [("Spinach", 150), ("Peanuts", 20), ("Onion", 20), ("Mustard oil", 10)],
    ),
}


class Command(BaseCommand):
    """Create or update demo ingredients and recipes (safe to run many times)."""

    help = "Add demo ingredients and recipes for the Recipe Box."

    def handle(self, *args, **options):
        """Save every ingredient, then every recipe with its ingredient amounts."""
        for name, (tag, price) in INGREDIENTS.items():
            Ingredient.objects.update_or_create(
                name=name,
                defaults={"allergen_tag": tag, "estimated_price_bdt": Decimal(price)},
            )

        for title, (description, items) in RECIPES.items():
            recipe, _ = Recipe.objects.update_or_create(
                title=title,
                defaults={
                    "description": description,
                    "instructions": "Cook all ingredients together. Serve hot.",
                    "servings_base": 1,
                    "has_unconfirmed_ingredients": False,
                },
            )
            for ingredient_name, grams in items:
                RecipeIngredient.objects.update_or_create(
                    recipe=recipe,
                    ingredient=Ingredient.objects.get(name=ingredient_name),
                    defaults={"quantity_per_serving": Decimal(grams), "unit": "g"},
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Ready: {len(INGREDIENTS)} ingredients, {len(RECIPES)} recipes."
            )
        )
