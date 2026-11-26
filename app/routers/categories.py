from fastapi import APIRouter, Query, status

from app.core.dependencies import DbSession
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.schemas.common import PaginatedResponse
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category",
)
async def create_category(data: CategoryCreate, db: DbSession):
    service = CategoryService(db)
    return await service.create_category(data)


@router.get(
    "/",
    response_model=PaginatedResponse[CategoryResponse],
    status_code=status.HTTP_200_OK,
    summary="List categories with pagination",
)
async def list_categories(
    db: DbSession,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    service = CategoryService(db)
    return await service.get_categories(page=page, size=size)


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a category by ID",
)
async def get_category(category_id: int, db: DbSession):
    service = CategoryService(db)
    return await service.get_category_by_id(category_id)


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a category by ID",
)
async def update_category(
    category_id: int, data: CategoryUpdate, db: DbSession
):
    service = CategoryService(db)
    return await service.update_category(category_id, data)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category by ID",
)
async def delete_category(category_id: int, db: DbSession):
    service = CategoryService(db)
    await service.delete_category(category_id)