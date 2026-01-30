import random
import string
from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import Header, HTTPException, status
from supabase import Client, create_client

from app.core.config import settings


def generate_share_code() -> str:
    """Generate a 9-digit numeric share code"""
    return ''.join(random.choices(string.digits, k=9))


def get_share_code_expiry(days: int = 3) -> datetime:
    """Get share code expiration datetime (default 3 days from now)"""
    return datetime.utcnow() + timedelta(days=days)


def is_share_code_valid(expires_at: datetime) -> bool:
    """Check if share code is still valid"""
    return datetime.utcnow() < expires_at


@dataclass
class AuthContext:
    """Authenticated request context with user_id, user object, and supabase client."""
    user_id: str
    user: object  # Supabase User object
    supabase: Client


async def get_auth_context(authorization: str = Header(...)) -> AuthContext:
    """
    Get authenticated context with user_id, user object, and supabase client.
    Use this instead of separate get_current_user_id and get_supabase dependencies.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )

    token = authorization.removeprefix("Bearer ")

    # Create client and set auth token
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    supabase.postgrest.auth(token)

    try:
        user_response = supabase.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        return AuthContext(
            user_id=user_response.user.id,
            user=user_response.user,
            supabase=supabase
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}"
        )
