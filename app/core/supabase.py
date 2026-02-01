from dataclasses import dataclass

from fastapi import Header, HTTPException, status
from supabase import create_client, Client

from app.core.config import settings


@dataclass
class AuthContext:
    """Authenticated request context with user_id, user object, and supabase client."""
    user_id: str
    user: object  # Supabase User object
    supabase: Client


async def get_auth_context(authorization: str = Header(...)) -> AuthContext:
    """
    Get authenticated context with user_id, user object, and supabase client.
    Uses postgrest.auth() to set the token for RLS policies.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )

    token = authorization.removeprefix("Bearer ")

    # Create client and set auth token for RLS
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


def get_supabase_service() -> Client:
    """Get Supabase service client for admin operations (bypasses RLS)."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
