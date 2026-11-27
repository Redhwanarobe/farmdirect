"""Business rules for farms."""

from django.core.exceptions import PermissionDenied


def get_own_farm(user):
    """Return the farm owned by this farmer, or block the request."""
    if getattr(user, "role", None) != "farmer":
        raise PermissionDenied("Only farmers can open this page.")
    farm = user.farms.filter(is_active=True).first()
    if farm is None:
        raise PermissionDenied("You do not have an active farm yet.")
    return farm
