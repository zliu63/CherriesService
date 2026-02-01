import random
import string
from datetime import datetime, timedelta


def generate_share_code() -> str:
    """Generate a 9-digit numeric share code."""
    return ''.join(random.choices(string.digits, k=9))


def get_share_code_expiry(days: int = 3) -> datetime:
    """Get share code expiration datetime (default 3 days from now)."""
    return datetime.utcnow() + timedelta(days=days)


def is_share_code_valid(expires_at: datetime) -> bool:
    """Check if share code is still valid."""
    return datetime.utcnow() < expires_at
