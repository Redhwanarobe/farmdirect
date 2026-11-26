from django.contrib import admin

from .models import (
    DeliverySlot,
    Ingredient,
    PantryItem,
    Recipe,
    RecipeIngredient,
    RecipeSubscription,
    UserAllergyPreference,
)


class RecipeIngredientInline(admin.TabularInline):
    """Inline editor for recipe ingredients."""

    model = RecipeIngredient
    extra = 1


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Admin configuration for Ingredient."""

    list_display = ("name", "allergen_tag", "estimated_price_bdt")
    list_filter = ("allergen_tag",)
    search_fields = ("name",)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Admin configuration for Recipe."""

    list_display = ("title", "servings_base", "has_unconfirmed_ingredients")
    list_filter = ("has_unconfirmed_ingredients",)
    search_fields = ("title",)
    inlines = [RecipeIngredientInline]


@admin.register(RecipeSubscription)
class RecipeSubscriptionAdmin(admin.ModelAdmin):
    """Admin configuration for RecipeSubscription."""

    list_display = (
        "user",
        "plan_type",
        "delivery_day",
        "servings",
        "budget_bdt",
        "status",
    )
    list_filter = ("plan_type", "status")


@admin.register(DeliverySlot)
class DeliverySlotAdmin(admin.ModelAdmin):
    """Admin configuration for DeliverySlot."""

    list_display = ("subscription", "delivery_date", "status", "locked_for_packing")
    list_filter = ("status", "locked_for_packing")


@admin.register(PantryItem)
class PantryItemAdmin(admin.ModelAdmin):
    """Admin configuration for PantryItem."""

    list_display = ("user", "ingredient", "quantity_label")


admin.site.register(UserAllergyPreference)
