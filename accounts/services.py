"""Business rules for user accounts."""

import re

from .models import User

BD_MOBILE_PATTERN = re.compile(r"^(?:\+?880|0)?(1[3-9]\d{8})$")


def normalize_bd_phone(raw_phone):
    """Return a Bangladeshi mobile number in +8801XXXXXXXXX form.

    Args:
        raw_phone: The number the user typed, such as "01712345678"
            or "+8801712345678".

    Returns:
        The number as "+8801712345678", or None if it is not a valid
        Bangladeshi mobile number.
    """
    digits = raw_phone.replace(" ", "").replace("-", "")
    match = BD_MOBILE_PATTERN.match(digits)
    if match is None:
        return None
    return "+880" + match.group(1)


def find_username(identifier):
    """Find the username for an email or Bangladeshi mobile number.

    Args:
        identifier: What the user typed in the login form.

    Returns:
        The matching username, or None if no account is found.
    """
    identifier = identifier.strip()
    phone = normalize_bd_phone(identifier)
    if phone:
        user = User.objects.filter(phone=phone).first()
    else:
        user = User.objects.filter(email__iexact=identifier).first()
    if user is None:
        user = User.objects.filter(username=identifier).first()
    if user is None:
        return None
    return user.username
