from django import forms

from .models import Ingredient, PantryItem, Recipe, RecipeSubscription

ALLERGEN_FORM_CHOICES = [
    ("nuts", "Nuts"),
    ("gluten", "Gluten"),
    ("dairy", "Dairy"),
    ("eggs", "Eggs"),
    ("soy", "Soy"),
    ("shellfish", "Shellfish"),
]


class RecipeBoxForm(forms.Form):
    """Form for selecting recipes, servings (1-12), budget, and delivery schedule."""

    plan_type = forms.ChoiceField(choices=RecipeSubscription.PLAN_CHOICES)
    delivery_day = forms.CharField(max_length=20, initial="Friday")
    servings = forms.IntegerField(min_value=1, max_value=12, initial=2)
    budget_bdt = forms.DecimalField(
        min_value=0, max_digits=8, decimal_places=2, initial=1500
    )
    selected_recipes = forms.ModelMultipleChoiceField(
        queryset=Recipe.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, *args, available_recipes=None, **kwargs):
        super().__init__(*args, **kwargs)
        if available_recipes is not None:
            ids = [r.id for r in available_recipes]
            self.fields["selected_recipes"].queryset = Recipe.objects.filter(
                id__in=ids
            )
        else:
            self.fields["selected_recipes"].queryset = Recipe.objects.all()


class AllergyPreferenceForm(forms.Form):
    """Form for choosing blocked allergens and specific blocked ingredients."""

    blocked_allergens = forms.MultipleChoiceField(
        choices=ALLERGEN_FORM_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    blocked_ingredients = forms.ModelMultipleChoiceField(
        queryset=Ingredient.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ordered = Ingredient.objects.order_by("name")
        self.fields["blocked_ingredients"].queryset = ordered


class PantryItemForm(forms.ModelForm):
    """Form for adding an ingredient to the user's pantry."""

    class Meta:
        model = PantryItem
        fields = ["ingredient", "quantity_label"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ingredient"].queryset = Ingredient.objects.order_by("name")
