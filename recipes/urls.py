from django.urls import path

from .views import (
    allergy_preferences_view,
    manage_subscription_view,
    pantry_recipes_view,
    recipe_box_view,
)

app_name = "recipes"

urlpatterns = [
    path("box/", recipe_box_view, name="recipe_box"),
    path("allergies/", allergy_preferences_view, name="allergy_preferences"),
    path("deliveries/", manage_subscription_view, name="manage_subscription"),
    path("pantry/", pantry_recipes_view, name="pantry_recipes"),
]
