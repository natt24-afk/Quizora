from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class TokenResponse(BaseModel):
    """
    Standard OAuth2 Bearer Token response.
    Satisfies Requirement #20 & #21 (OAuth2 and Bearer Token authentication).
    """
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    role: UserRole


class TokenPayload(BaseModel):
    """Internal decoded JWT payload."""
    sub: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None


class UserRegisterRequest(BaseModel):
    """User registration schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)
    role: UserRole = Field(default=UserRole.STUDENT, description="admin, teacher, or student")


class SessionResponse(BaseModel):
    """
    Active database session information.
    Satisfies Requirement #24 (Session-related information management).
    """
    id: int
    user_id: int
    session_token: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)