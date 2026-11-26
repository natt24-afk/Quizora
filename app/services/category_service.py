import math
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.schemas.common import PaginatedResponse


class CategoryService:
    def __init__(self, db: AsyncSession):
        self.repository = CategoryRepository(db)

    async def create_category(self, data: CategoryCreate) -> Category:
        """Create a category if the name is not already taken."""
        existing = await self.repository.get_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category '{data.name}' already exists.",
            )
        return await self.repository.create(data)

    async def get_category_by_id(self, category_id: int) -> Category:
        """Fetch category or raise 404."""
        category = await self.repository.get_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found.",
            )
        return category

    async def get_categories(
        self, page: int = 1, size: int = 20
    ) -> PaginatedResponse[CategoryResponse]:
        """Fetch paginated categories with metadata."""
        skip = (page - 1) * size
        items, total = await self.repository.get_all(skip=skip, limit=size)
        total_pages = math.ceil(total / size) if size > 0 else 0

        return PaginatedResponse[CategoryResponse](
            items=[CategoryResponse.model_validate(c) for c in items],
            total=total,
            page=page,
            size=size,
            pages=total_pages,
        )

    async def update_category(self, category_id: int, data: CategoryUpdate) -> Category:
        """Update category fields with duplicate name check."""
        category = await self.get_category_by_id(category_id)

        # If name is being changed, verify it doesn't collide with another category
        if data.name and data.name != category.name:
            existing = await self.repository.get_by_name(data.name)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Category name '{data.name}' is already in use.",
                )

        return await self.repository.update(category, data)

    async def delete_category(self, category_id: int) -> None:
        """Delete category or raise 404."""
        category = await self.get_category_by_id(category_id)
        await self.repository.delete(category)