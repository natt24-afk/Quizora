from typing import Optional
from fastapi import APIRouter, Query, status

from app.core.dependencies import DbSession
from app.models.user import UserRole
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
)
async def create_user(data: UserCreate, db: DbSession):
    service = UserService(db)
    return await service.create_user(data)


@router.get(
    "/",
    response_model=PaginatedResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="List users with pagination and role filtering",
)
async def list_users(
    db: DbSession,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    role: Optional[UserRole] = Query(None, description="Filter by role (admin, teacher, student)"),
):
    service = UserService(db)
    return await service.get_users(page=page, size=size, role=role)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user by ID",
)
async def get_user(user_id: int, db: DbSession):
    service = UserService(db)
    return await service.get_user_by_id(user_id)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user by ID",
)
async def update_user(user_id: int, data: UserUpdate, db: DbSession):
    service = UserService(db)
    return await service.update_user(user_id, data)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user by ID",
)
async def delete_user(user_id: int, db: DbSession):
    service = UserService(db)
    await service.delete_user(user_id)