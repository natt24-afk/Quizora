from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    generate_session_token,
)
from app.models.user import User
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse, UserRegisterRequest
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)
        self.session_repo = SessionRepository(db)

    async def register_user(self, data: UserRegisterRequest) -> User:
        """Register a new user with duplicate checks and Argon2 hashing."""
        if await self.user_repo.get_by_username(data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{data.username}' is already taken.",
            )
        if await self.user_repo.get_by_email(data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{data.email}' is already registered.",
            )

        user_create = UserCreate(
            username=data.username,
            email=data.email,
            full_name=data.full_name,
            password=data.password,
            role=data.role,
        )
        hashed_pwd = hash_password(data.password)
        return await self.user_repo.create(user_create, hashed_password=hashed_pwd)

    async def authenticate_user(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[TokenResponse, str]:
        """
        Validates credentials, issues JWT Bearer token, and creates a database session.
        Returns (TokenResponse, session_token).
        """
        # Fetch user by username
        user = await self.user_repo.get_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        # 1. Create JWT Access Token
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.value,
        }
        access_token = create_access_token(data=token_data)

        # 2. Create Database Session & Cookie Token
        session_token = generate_session_token()
        session_expires = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        await self.session_repo.create_session(
            user_id=user.id,
            session_token=session_token,
            expires_at=session_expires,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        token_response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id,
            username=user.username,
            role=user.role,
        )
        return token_response, session_token

    async def logout_session(self, session_token: Optional[str]) -> None:
        """Revokes session from database."""
        if session_token:
            await self.session_repo.delete_session(session_token)