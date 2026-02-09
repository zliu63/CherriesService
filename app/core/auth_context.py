from fastapi import Header, HTTPException, status
from supabase_auth.types import User as _SupabaseUser

from app.core.logging import logger
from app.core.supabase import get_supabase_client

# Type alias for Supabase User - import this instead of supabase_auth.types.User
CherriesUser = _SupabaseUser


async def get_user(authorization: str = Header(...)) -> CherriesUser:
    """
    Validate user token and return user object.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )

    token = authorization.removeprefix("Bearer ")
    supabase = get_supabase_client()

    try:
        user_response = supabase.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        return user_response.user

    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Auth failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}"
        )
