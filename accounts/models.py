"""Database models for FarmDirect user accounts."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """A FarmDirect user who can log in with a username or phone number."""

    class Role(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        FARMER = "farmer", "Farmer"
        RESTAURANT = "restaurant", "Restaurant"

    phone = models.CharField(max_length=14, unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)

    def __str__(self):
        return self.username
