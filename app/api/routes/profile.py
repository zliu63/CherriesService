from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from app.core.supabase import get_supabase_service
from app.core.utils import AuthContext, get_auth_context
from app.schemas.user import UserResponse, UserUpdate, AvatarData

router = APIRouter(prefix="/profile", tags=["Profile"])



@router.get("", response_model=UserResponse)
async def get_profile(
    auth: AuthContext = Depends(get_auth_context)
):
    """Get current user profile"""
    try:
        # Extract avatar from user_metadata
        avatar_data = auth.user.user_metadata.get("avatar")
        avatar = None
        if avatar_data and isinstance(avatar_data, dict):
            avatar = AvatarData(**avatar_data)

        user = UserResponse(
            id=auth.user.id,
            email=auth.user.email,
            username=auth.user.user_metadata.get("username"),
            avatar=avatar,
            created_at=auth.user.created_at,
            updated_at=auth.user.updated_at
        )

        return user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch("", response_model=UserResponse)
async def update_profile(
    update_data: UserUpdate,
    auth: AuthContext = Depends(get_auth_context),
    service_supabase: Client = Depends(get_supabase_service)
):
    """Update user profile (avatar, username)"""
    try:
        # Get current user metadata
        user_metadata = dict(auth.user.user_metadata) if auth.user.user_metadata else {}

        # Update username if provided
        if update_data.username is not None:
            user_metadata["username"] = update_data.username

        # Update avatar if provided
        if update_data.avatar is not None:
            user_metadata["avatar"] = update_data.avatar.model_dump()

        # Update user metadata using service client (admin privileges)
        updated_user = service_supabase.auth.admin.update_user_by_id(
            auth.user_id,
            {"user_metadata": user_metadata}
        )

        # Extract avatar from updated metadata
        avatar_data = updated_user.user.user_metadata.get("avatar") if updated_user.user.user_metadata else None
        avatar = None
        if avatar_data and isinstance(avatar_data, dict):
            avatar = AvatarData(**avatar_data)

        user = UserResponse(
            id=updated_user.user.id,
            email=updated_user.user.email,
            username=updated_user.user.user_metadata.get("username") if updated_user.user.user_metadata else None,
            avatar=avatar,
            created_at=updated_user.user.created_at,
            updated_at=updated_user.user.updated_at
        )

        return user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
