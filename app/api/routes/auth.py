from fastapi import APIRouter, Depends, HTTPException, status
from supabase_auth.errors import AuthApiError

from app.core.auth_context import CherriesUser, get_user
from app.core.logging import logger
from app.core.supabase import SupabaseClient, get_supabase_client, get_anon_client
from app.schemas import UserCreate, UserLogin, Token, UserResponse, RefreshTokenRequest
from app.schemas.user import AvatarData

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    supabase: SupabaseClient = Depends(get_supabase_client)
):
    """Register a new user"""
    try:
        # Default avatar for new users
        default_avatar = {
            "type": "emoji",
            "value": "🐶"
        }

        # Create user via Admin API (auto-confirms, skips confirmation email)
        admin_response = supabase.auth.admin.create_user({
            "email": user_data.email,
            "password": user_data.password,
            "email_confirm": True,
            "user_metadata": {
                "username": user_data.username,
                "avatar": default_avatar
            }
        })
        if not admin_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )

        # Sign in to get a session with tokens
        anon = get_anon_client()
        login_response = anon.auth.sign_in_with_password({
            "email": user_data.email,
            "password": user_data.password
        })

        user = UserResponse(
            id=admin_response.user.id,
            email=admin_response.user.email,
            username=user_data.username,
            avatar=AvatarData(**default_avatar),
            created_at=admin_response.user.created_at,
            updated_at=admin_response.user.updated_at
        )

        return Token(
            access_token=login_response.session.access_token,
            refresh_token=login_response.session.refresh_token,
            token_type="bearer",
            user=user
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Register failed for %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    supabase: SupabaseClient = Depends(get_anon_client)
):
    """Login user"""
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Extract avatar from user_metadata
        avatar_data = auth_response.user.user_metadata.get("avatar")
        avatar = None
        if avatar_data and isinstance(avatar_data, dict):
            avatar = AvatarData(**avatar_data)

        user = UserResponse(
            id=auth_response.user.id,
            email=auth_response.user.email,
            username=auth_response.user.user_metadata.get("username"),
            avatar=avatar,
            created_at=auth_response.user.created_at,
            updated_at=auth_response.user.updated_at
        )

        return Token(
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
            token_type="bearer",
            user=user
        )

    except Exception as e:
        logger.warning("Login failed for %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    supabase: SupabaseClient = Depends(get_anon_client)
):
    """Refresh access token using refresh token"""
    logger.debug("Token refresh requested")
    try:
        auth_response = supabase.auth.refresh_session(request.refresh_token)

        if not auth_response.user or not auth_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        # Extract avatar from user_metadata
        avatar_data = auth_response.user.user_metadata.get("avatar")
        avatar = None
        if avatar_data and isinstance(avatar_data, dict):
            avatar = AvatarData(**avatar_data)

        user = UserResponse(
            id=auth_response.user.id,
            email=auth_response.user.email,
            username=auth_response.user.user_metadata.get("username"),
            avatar=avatar,
            created_at=auth_response.user.created_at,
            updated_at=auth_response.user.updated_at
        )

        return Token(
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
            token_type="bearer",
            user=user
        )

    except HTTPException:
        raise
    except AuthApiError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    except Exception as e:
        logger.error("Token refresh failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to refresh token"
        )


@router.post("/logout")
async def logout(
    user: CherriesUser = Depends(get_user),
    supabase: SupabaseClient = Depends(get_anon_client)
):
    """Logout user"""
    logger.info("Logout: user_id=%s", user.id)
    try:
        supabase.auth.sign_out()
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error("Logout failed for user_id=%s: %s", user.id, e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
