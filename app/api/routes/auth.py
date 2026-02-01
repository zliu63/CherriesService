from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from app.core.supabase import AuthContext, get_auth_context, get_supabase_service
from app.schemas import UserCreate, UserLogin, Token, UserResponse
from app.schemas.user import AvatarData

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    supabase: Client = Depends(get_supabase_service)
):
    """Register a new user"""
    try:
        # Default avatar for new users
        default_avatar = {
            "type": "emoji",
            "value": "🐶"
        }

        # Sign up user with Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "username": user_data.username,
                    "avatar": default_avatar
                }
            }
        })

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )

        user = UserResponse(
            id=auth_response.user.id,
            email=auth_response.user.email,
            username=user_data.username,
            avatar=AvatarData(**default_avatar),
            created_at=auth_response.user.created_at,
            updated_at=auth_response.user.updated_at
        )

        return Token(
            access_token=auth_response.session.access_token,
            token_type="bearer",
            user=user
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    supabase: Client = Depends(get_supabase_service)
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
            token_type="bearer",
            user=user
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


@router.post("/logout")
async def logout(auth: AuthContext = Depends(get_auth_context)):
    """Logout user"""
    try:
        auth.supabase.auth.sign_out()
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
