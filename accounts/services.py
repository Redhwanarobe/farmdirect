"""Business rules for user accounts."""

import re
import secrets
from datetime import datetime, timedelta

from django.utils import timezone

from core.constants import INACTIVE_DAYS, VERIFY_CODE_MINUTES

from .models import User

BD_MOBILE_PATTERN = re.compile(r"^(?:\+?880|0)?(1[3-9]\d{8})$")
CODE_EXPIRED = "Verification code expired – request a new code."
WRONG_CODE = "Wrong code. Please try again."
SESSION_KEYS = ("verify_user_id", "verify_code", "verify_expires")


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


def needs_reverification(user, now=None):
    """Return True if the user has not logged in for more than a year.

    Args:
        user: The user who is trying to log in.
        now: The current time. Tests can pass a fixed time.

    Returns:
        True if a verification code is needed before login.
    """
    now = now or timezone.now()
    if user.last_login is None:
        return False
    return now - user.last_login > timedelta(days=INACTIVE_DAYS)


def start_reverification(session, user, now=None):
    """Make a 6-digit code, keep it in the session and "send" it.

    The SMS is simulated: the code is printed in the terminal.

    Args:
        session: The browser session (request.session).
        user: The user who must verify.
        now: The current time. Tests can pass a fixed time.

    Returns:
        The 6-digit code.
    """
    now = now or timezone.now()
    code = f"{secrets.randbelow(1_000_000):06d}"
    expires = now + timedelta(minutes=VERIFY_CODE_MINUTES)
    session["verify_user_id"] = user.pk
    session["verify_code"] = code
    session["verify_expires"] = expires.isoformat()
    print(f"[FarmDirect SMS] Code for {user.phone or user.email}: {code}")
    return code


def check_reverification(session, code, now=None):
    """Check the code the user typed.

    Args:
        session: The browser session (request.session).
        code: The code the user typed.
        now: The current time. Tests can pass a fixed time.

    Returns:
        A pair (user, error). If the code is right, user is set and
        error is None. Otherwise user is None and error is a message.
    """
    now = now or timezone.now()
    user_id = session.get("verify_user_id")
    expires = session.get("verify_expires")
    if user_id is None or expires is None:
        return None, CODE_EXPIRED
    if now > datetime.fromisoformat(expires):
        return None, CODE_EXPIRED
    if not secrets.compare_digest(code, session.get("verify_code", "")):
        return None, WRONG_CODE
    for key in SESSION_KEYS:
        session.pop(key, None)
    return User.objects.get(pk=user_id), None


def home_url_for(user):
    """Return the page a user should see right after logging in."""
    if user.is_staff:
        return "admin:index"
    if user.role == "farmer" and user.farms.filter(is_active=True).exists():
        return "farms:dashboard"
    if user.role == "restaurant":
        return "bulk:dashboard"
    return "core:home"
