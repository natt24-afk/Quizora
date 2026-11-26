import math
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserCreate, UserUpdate, UserResponse


class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)

    async def create_user(self, data: UserCreate) -> User:
        """Create a new user with duplicate checks and password hashing."""
        # Check duplicate username
        if await self.repository.get_by_username(data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{data.username}' is already taken.",
            )

        # Check duplicate email
        if await self.repository.get_by_email(data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{data.email}' is already registered.",
            )

        # Hash password securely using Argon2
        hashed_pwd = hash_password(data.password)
        return await self.repository.create(data, hashed_password=hashed_pwd)

    async def get_user_by_id(self, user_id: int) -> User:
        """Retrieve user by ID or raise 404."""
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found.",
            )
        return user

    async def get_users(
        self, page: int = 1, size: int = 20, role: Optional[UserRole] = None
    ) -> PaginatedResponse[UserResponse]:
        """List users with pagination and optional role filtering."""
        skip = (page - 1) * size
        items, total = await self.repository.get_all(skip=skip, limit=size, role=role)
        total_pages = math.ceil(total / size) if size > 0 else 0

        return PaginatedResponse[UserResponse](
            items=[UserResponse.model_validate(u) for u in items],
            total=total,
            page=page,
            size=size,
            pages=total_pages,
        )

    async def update_user(self, user_id: int, data: UserUpdate) -> User:
        """Update user profile or password with uniqueness checks."""
        user = await self.get_user_by_id(user_id)

        # Check email uniqueness if being changed
        if data.email and data.email != user.email:
            if await self.repository.get_by_email(data.email):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Email '{data.email}' is already in use.",
                )

        # Hash new password if provided
        hashed_pwd = hash_password(data.password) if data.password else None
        return await self.repository.update(user, data, hashed_password=hashed_pwd)

    async def delete_user(self, user_id: int) -> None:
        """Delete user or raise 404."""
        user = await self.get_user_by_id(user_id)
        await self.repository.delete(user)