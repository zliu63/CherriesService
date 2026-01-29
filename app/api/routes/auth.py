from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from app.core.supabase import get_supabase
from app.schemas import UserCreate, UserLogin, Token, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    supabase: Client = Depends(get_supabase)
):
    """Register a new user"""
    try:
        # Sign up user with Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "username": user_data.username
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
    supabase: Client = Depends(get_supabase)
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

        user = UserResponse(
            id=auth_response.user.id,
            email=auth_response.user.email,
            username=auth_response.user.user_metadata.get("username"),
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
async def logout(supabase: Client = Depends(get_supabase)):
    """Logout user"""
    try:
        supabase.auth.sign_out()
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
