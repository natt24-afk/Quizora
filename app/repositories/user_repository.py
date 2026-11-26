from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_all(
        self, skip: int = 0, limit: int = 20, role: Optional[UserRole] = None
    ) -> tuple[List[User], int]:
        query = select(User)
        count_query = select(func.count(User.id))

        if role:
            query = query.where(User.role == role)
            count_query = count_query.where(User.role == role)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        result = await self.db.execute(query.order_by(User.id.asc()).offset(skip).limit(limit))
        items = list(result.scalars().all())
        return items, total

    async def create(self, data: UserCreate, hashed_password: str) -> User:
        user = User(
            username=data.username,
            email=data.email,
            full_name=data.full_name,
            hashed_password=hashed_password,
            role=data.role,
            is_active=True,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(
        self, user: User, data: UserUpdate, hashed_password: Optional[str] = None
    ) -> User:
        update_data = data.model_dump(exclude_unset=True)
        if "password" in update_data:
            del update_data["password"]

        for key, value in update_data.items():
            setattr(user, key, value)

        if hashed_password:
            user.hashed_password = hashed_password

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.db.delete(user)
        await self.db.commit()