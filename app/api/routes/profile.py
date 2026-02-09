from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth_context import CherriesUser, get_user
from app.core.logging import logger
from app.core.supabase import SupabaseClient, get_supabase_client
from app.schemas.user import UserResponse, UserUpdate, AvatarData

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("", response_model=UserResponse)
async def get_profile(user: CherriesUser = Depends(get_user)):
    """Get current user profile"""
    try:
        # Extract avatar from user_metadata
        avatar_data = user.user_metadata.get("avatar")
        avatar = None
        if avatar_data and isinstance(avatar_data, dict):
            avatar = AvatarData(**avatar_data)

        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.user_metadata.get("username"),
            avatar=avatar,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch("", response_model=UserResponse)
async def update_profile(
    update_data: UserUpdate,
    user: CherriesUser = Depends(get_user),
    supabase: SupabaseClient = Depends(get_supabase_client)
):
    """Update user profile (avatar, username)"""
    logger.info("Update profile: user_id=%s", user.id)
    try:
        # Get current user metadata
        user_metadata = dict(user.user_metadata) if user.user_metadata else {}

        # Update username if provided
        if update_data.username is not None:
            user_metadata["username"] = update_data.username

        # Update avatar if provided
        if update_data.avatar is not None:
            user_metadata["avatar"] = update_data.avatar.model_dump()

        # Update user metadata using service client (admin privileges)
        updated_user = supabase.auth.admin.update_user_by_id(
            user.id,
            {"user_metadata": user_metadata}
        )

        # Extract avatar from updated metadata
        avatar_data = updated_user.user.user_metadata.get("avatar") if updated_user.user.user_metadata else None
        avatar = None
        if avatar_data and isinstance(avatar_data, dict):
            avatar = AvatarData(**avatar_data)

        return UserResponse(
            id=updated_user.user.id,
            email=updated_user.user.email,
            username=updated_user.user.user_metadata.get("username") if updated_user.user.user_metadata else None,
            avatar=avatar,
            created_at=updated_user.user.created_at,
            updated_at=updated_user.user.updated_at
        )

    except Exception as e:
        logger.error("Update profile failed for user_id=%s: %s", user.id, e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
