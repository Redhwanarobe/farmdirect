from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from .models import (
    DeliverySlot,
    Ingredient,
    PantryItem,
    Recipe,
    RecipeIngredient,
    RecipeSubscription,
    UserAllergyPreference,
)


def calculate_recipe_cost_bdt(recipe: Recipe, servings: int) -> Decimal:
    """Return total estimated BDT cost for a recipe scaled to requested servings."""
    if servings < 1:
        servings = 1
    total = Decimal("0.00")
    items = RecipeIngredient.objects.filter(recipe=recipe).select_related("ingredient")
    for item in items:
        line_cost = Decimal(item.quantity_per_serving) * Decimal(servings)
        unit_price = item.ingredient.estimated_price_bdt
        total += line_cost * unit_price * Decimal("0.01")
    return total.quantize(Decimal("0.01"))


def calculate_box_cost_and_swaps(
    selected_recipes, servings: int, budget_bdt: Decimal
) -> dict:
    """Calculate total box cost, compare with budget, and suggest lower-cost swaps."""
    recipe_list = list(selected_recipes)
    total_cost = Decimal("0.00")
    per_recipe = []
    for recipe in recipe_list:
        cost = calculate_recipe_cost_bdt(recipe, servings)
        total_cost += cost
        per_recipe.append({"recipe": recipe, "cost": cost})

    total_cost = total_cost.quantize(Decimal("0.01"))
    over_budget = total_cost > budget_bdt

    selected_ids = {r.id for r in recipe_list}
    swaps = []
    if over_budget:
        candidates = (
            Recipe.objects.filter(has_unconfirmed_ingredients=False)
            .exclude(id__in=selected_ids)
        )
        for candidate in candidates:
            cand_cost = calculate_recipe_cost_bdt(candidate, servings)
            swaps.append({"recipe": candidate, "cost": cand_cost})
        swaps.sort(key=lambda entry: entry["cost"])

    return {
        "total_cost": total_cost,
        "over_budget": over_budget,
        "per_recipe": per_recipe,
        "swaps": swaps[:3],
    }


def get_user_blocked_data(user) -> tuple[set[str], set[int]]:
    """Return (blocked_allergen_set, blocked_ingredient_id_set) for a user."""
    if not user or not user.is_authenticated:
        return set(), set()
    pref = UserAllergyPreference.objects.filter(user=user).first()
    if not pref:
        return set(), set()
    allergens = {str(a).lower() for a in (pref.blocked_allergens or [])}
    ingredient_ids = set(pref.blocked_ingredients.values_list("id", flat=True))
    return allergens, ingredient_ids


def get_safe_recipes(user) -> list[Recipe]:
    """Return recipes safe from allergies, blocked ingredients, and unconfirmed data."""
    blocked_allergens, blocked_ing_ids = get_user_blocked_data(user)
    safe = []
    recipes = (
        Recipe.objects.filter(has_unconfirmed_ingredients=False)
        .prefetch_related("recipeingredient_set__ingredient")
    )
    for recipe in recipes:
        recipe_ings = list(recipe.recipeingredient_set.all())
        unsafe = False
        for ri in recipe_ings:
            ing = ri.ingredient
            if ing.id in blocked_ing_ids:
                unsafe = True
                break
            if (ing.allergen_tag or "none").lower() in blocked_allergens:
                unsafe = True
                break
        if not unsafe:
            safe.append(recipe)
    return safe


def create_initial_delivery_slots(
    subscription: RecipeSubscription, count: int = 4
) -> list[DeliverySlot]:
    """Create upcoming weekly delivery slots for a newly confirmed subscription."""
    slots = []
    start_date = timezone.localdate() + timedelta(days=3)
    for idx in range(count):
        slot_date = start_date + timedelta(weeks=idx)
        slot = DeliverySlot.objects.create(
            subscription=subscription,
            delivery_date=slot_date,
            status="scheduled",
            locked_for_packing=False,
        )
        slots.append(slot)
    return slots


def can_skip_delivery_slot(slot: DeliverySlot) -> tuple[bool, str]:
    """Check whether a slot can be skipped (not locked and not already delivered)."""
    if slot.status == "delivered":
        return False, "This delivery has already been delivered."
    if slot.locked_for_packing or slot.status == "locked":
        return False, "Cannot skip: this delivery is locked for packing."
    if slot.status == "skipped":
        return False, "This delivery slot is already skipped."
    return True, "Delivery skipped."


def get_pantry_suggestions(user) -> list[dict]:
    """Match user's pantry items against allergy-safe recipes."""
    pantry_ids = set(
        PantryItem.objects.filter(user=user).values_list("ingredient_id", flat=True)
    )
    safe_recipes = get_safe_recipes(user)
    suggestions = []
    for recipe in safe_recipes:
        items = list(recipe.recipeingredient_set.select_related("ingredient").all())
        if not items:
            continue
        matched = [ri.ingredient for ri in items if ri.ingredient_id in pantry_ids]
        missing = [ri.ingredient for ri in items if ri.ingredient_id not in pantry_ids]
        if matched:
            suggestions.append(
                {
                    "recipe": recipe,
                    "matched": matched,
                    "missing": missing,
                    "match_count": len(matched),
                    "missing_count": len(missing),
                }
            )
    suggestions.sort(key=lambda item: (-item["match_count"], item["missing_count"]))
    return suggestions


def get_all_ingredients_ordered():
    """Return all ingredients sorted by name."""
    return Ingredient.objects.order_by("name")
