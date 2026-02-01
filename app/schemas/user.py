from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, Literal
from datetime import datetime


class AvatarData(BaseModel):
    type: Literal["emoji", "preset", "custom"]
    value: str


class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: str
    avatar: Optional[AvatarData] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    user_id: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    avatar: Optional[AvatarData] = None
