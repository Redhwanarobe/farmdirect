"""Farms and the products they sell."""

from django.conf import settings
from django.db import models


class Farm(models.Model):
    """A farm near Dhaka owned by a farmer."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="farms",
        limit_choices_to={"role": "farmer"},
    )
    name = models.CharField(max_length=120)
    area = models.CharField(max_length=80, help_text="For example: Savar, Mirpur")
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    """Something a farm sells, with its price in Taka and stock."""

    class Unit(models.TextChoices):
        KG = "kg", "kg"
        PIECE = "piece", "piece"
        DOZEN = "dozen", "dozen"

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=60, help_text="For example: Vegetables")
    unit = models.CharField(max_length=10, choices=Unit.choices, default=Unit.KG)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.farm})"

    @property
    def in_stock(self):
        """Return True if some stock is left."""
        return self.stock > 0
