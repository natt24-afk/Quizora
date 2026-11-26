from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, category_id: int) -> Optional[Category]:
        """Fetch a category by its primary key ID."""
        result = await self.db.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalars().first()

    async def get_by_name(self, name: str) -> Optional[Category]:
        """Fetch a category by its unique name."""
        result = await self.db.execute(
            select(Category).where(Category.name == name)
        )
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 20) -> tuple[List[Category], int]:
        """Fetch a paginated list of categories and the total count."""
        # Total count query
        count_result = await self.db.execute(select(func.count(Category.id)))
        total = count_result.scalar() or 0

        # Paginated items query
        result = await self.db.execute(
            select(Category)
            .order_by(Category.id.asc())
            .offset(skip)
            .limit(limit)
        )
        items = list(result.scalars().all())
        return items, total

    async def create(self, data: CategoryCreate) -> Category:
        """Create and commit a new category."""
        category = Category(
            name=data.name,
            description=data.description,
        )
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def update(self, category: Category, data: CategoryUpdate) -> Category:
        """Update fields of an existing category."""
        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(category, key, value)

        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def delete(self, category: Category) -> None:
        """Delete an existing category."""
        await self.db.delete(category)
        await self.db.commit()