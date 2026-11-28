from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AllergyPreferenceForm, PantryItemForm, RecipeBoxForm
from .models import (
    DeliverySlot,
    Ingredient,
    PantryItem,
    RecipeSubscription,
    UserAllergyPreference,
)
from .services import (
    calculate_box_cost_and_swaps,
    can_skip_delivery_slot,
    create_initial_delivery_slots,
    get_pantry_suggestions,
    get_safe_recipes,
)


@login_required
def recipe_box_view(request):
    """Story 6: Recipe box builder, budget check, and demo checkout."""
    safe_recipes = get_safe_recipes(request.user)
    initial_data = {
        "plan_type": "weekly",
        "delivery_day": "Friday",
        "servings": 2,
        "budget_bdt": 1500,
        "selected_recipes": safe_recipes[:2],
    }
    if request.method == "POST":
        form = RecipeBoxForm(request.POST, available_recipes=safe_recipes)
        if form.is_valid():
            plan_type = form.cleaned_data["plan_type"]
            delivery_day = form.cleaned_data["delivery_day"]
            servings = form.cleaned_data["servings"]
            budget_bdt = form.cleaned_data["budget_bdt"]
            selected = list(form.cleaned_data["selected_recipes"])

            summary = calculate_box_cost_and_swaps(selected, servings, budget_bdt)
            if "confirm_subscription" in request.POST:
                subscription = RecipeSubscription.objects.create(
                    user=request.user,
                    plan_type=plan_type,
                    delivery_day=delivery_day,
                    servings=servings,
                    budget_bdt=budget_bdt,
                    status="active",
                )
                subscription.selected_recipes.set(selected)
                create_initial_delivery_slots(subscription, count=4)
                messages.success(
                    request,
                    "Subscription confirmed (Demo) and delivery slots created.",
                )
                return redirect("recipes:manage_subscription")
            return render(
                request,
                "recipes/recipe_box.html",
                {
                    "form": form,
                    "summary": summary,
                    "safe_recipes": safe_recipes,
                },
            )
    else:
        form = RecipeBoxForm(initial=initial_data, available_recipes=safe_recipes)

    preview_recipes = form.initial.get("selected_recipes", [])
    summary = calculate_box_cost_and_swaps(
        preview_recipes,
        form.initial.get("servings", 2),
        form.initial.get("budget_bdt", 1500),
    )
    return render(
        request,
        "recipes/recipe_box.html",
        {
            "form": form,
            "summary": summary,
            "safe_recipes": safe_recipes,
        },
    )


@login_required
def allergy_preferences_view(request):
    """Story 7: Save blocked allergens/ingredients and view safe recipes."""
    pref, _ = UserAllergyPreference.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = AllergyPreferenceForm(request.POST)
        if form.is_valid():
            pref.blocked_allergens = form.cleaned_data["blocked_allergens"]
            pref.save()
            pref.blocked_ingredients.set(form.cleaned_data["blocked_ingredients"])
            messages.success(request, "Allergy and dietary preferences updated.")
            return redirect("recipes:allergy_preferences")
    else:
        form = AllergyPreferenceForm(
            initial={
                "blocked_allergens": pref.blocked_allergens or [],
                "blocked_ingredients": pref.blocked_ingredients.all(),
            }
        )

    safe_recipes = get_safe_recipes(request.user)
    return render(
        request,
        "recipes/allergy_preferences.html",
        {
            "form": form,
            "safe_recipes": safe_recipes,
            "pref": pref,
        },
    )


@login_required
def manage_subscription_view(request):
    """Story 8: View slots and skip, pause, resume, or cancel subscription."""
    subscription = (
        RecipeSubscription.objects.filter(user=request.user)
        .order_by("-created_at")
        .first()
    )
    slots = []
    if subscription:
        slots = list(subscription.delivery_slots.order_by("delivery_date"))

    if request.method == "POST" and subscription:
        action = request.POST.get("action", "")
        if action == "skip_slot":
            slot_id = request.POST.get("slot_id")
            slot = get_object_or_404(
                DeliverySlot, id=slot_id, subscription=subscription
            )
            allowed, reason = can_skip_delivery_slot(slot)
            if allowed:
                slot.status = "skipped"
                slot.save(update_fields=["status"])
                messages.success(
                    request, f"Delivery on {slot.delivery_date} has been skipped."
                )
            else:
                messages.warning(request, reason)
        elif action == "pause_sub":
            subscription.status = "paused"
            subscription.save(update_fields=["status"])
            messages.info(
                request,
                "Subscription paused. Future deliveries are on hold.",
            )
        elif action == "resume_sub":
            subscription.status = "active"
            subscription.save(update_fields=["status"])
            messages.success(request, "Subscription resumed and active.")
        elif action == "cancel_sub":
            subscription.status = "cancelled"
            subscription.save(update_fields=["status"])
            messages.warning(request, "Subscription cancelled.")
        return redirect("recipes:manage_subscription")

    return render(
        request,
        "recipes/manage_subscription.html",
        {
            "subscription": subscription,
            "slots": slots,
        },
    )


@login_required
def pantry_recipes_view(request):
    """Story 11: Manage pantry items, view safe matches, and shopping list."""
    shopping_list_ids = set(request.session.get("pantry_shopping_list", []))

    if request.method == "POST":
        action = request.POST.get("action", "add_item")
        if action == "add_item":
            form = PantryItemForm(request.POST)
            if form.is_valid():
                ing = form.cleaned_data["ingredient"]
                qty = form.cleaned_data["quantity_label"]
                PantryItem.objects.update_or_create(
                    user=request.user,
                    ingredient=ing,
                    defaults={"quantity_label": qty},
                )
                messages.success(request, f"Added {ing.name} to your pantry.")
                return redirect("recipes:pantry_recipes")
        elif action == "remove_item":
            item_id = request.POST.get("item_id")
            PantryItem.objects.filter(id=item_id, user=request.user).delete()
            messages.info(request, "Removed item from your pantry.")
            return redirect("recipes:pantry_recipes")
        elif action == "add_missing":
            missing_ids = request.POST.getlist("missing_ids")
            for raw_id in missing_ids:
                if raw_id.isdigit():
                    shopping_list_ids.add(int(raw_id))
            request.session["pantry_shopping_list"] = sorted(shopping_list_ids)
            messages.success(
                request, "Missing ingredients added to your recipes shopping list."
            )
            return redirect("recipes:pantry_recipes")
        elif action == "clear_shopping":
            request.session["pantry_shopping_list"] = []
            messages.info(request, "Shopping list cleared.")
            return redirect("recipes:pantry_recipes")
    else:
        form = PantryItemForm()

    pantry_items = list(
        PantryItem.objects.filter(user=request.user)
        .select_related("ingredient")
        .order_by("ingredient__name")
    )
    suggestions = get_pantry_suggestions(request.user)
    shopping_ingredients = list(
        Ingredient.objects.filter(id__in=shopping_list_ids).order_by("name")
    )

    return render(
        request,
        "recipes/pantry_recipes.html",
        {
            "form": form,
            "pantry_items": pantry_items,
            "suggestions": suggestions,
            "shopping_ingredients": shopping_ingredients,
        },
    )

