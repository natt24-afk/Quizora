from typing import Optional
from fastapi import APIRouter, Query, status

from app.core.dependencies import DbSession
from app.schemas.common import PaginatedResponse
from app.schemas.quiz import QuizCreate, QuizUpdate, QuizResponse
from app.services.quiz_service import QuizService

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])


@router.post(
    "/",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new quiz",
)
async def create_quiz(data: QuizCreate, db: DbSession):
    service = QuizService(db)
    return await service.create_quiz(data)


@router.get(
    "/",
    response_model=PaginatedResponse[QuizResponse],
    status_code=status.HTTP_200_OK,
    summary="List quizzes with search and filters",
)
async def list_quizzes(
    db: DbSession,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    is_published: Optional[bool] = Query(None, description="Filter by published status"),
    search: Optional[str] = Query(None, description="Search quiz title"),
):
    service = QuizService(db)
    return await service.get_quizzes(
        page=page,
        size=size,
        category_id=category_id,
        is_published=is_published,
        search=search,
    )


@router.get(
    "/{quiz_id}",
    response_model=QuizResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a quiz by ID",
)
async def get_quiz(quiz_id: int, db: DbSession):
    service = QuizService(db)
    return await service.get_quiz_by_id(quiz_id)


@router.put(
    "/{quiz_id}",
    response_model=QuizResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a quiz by ID",
)
async def update_quiz(quiz_id: int, data: QuizUpdate, db: DbSession):
    service = QuizService(db)
    return await service.update_quiz(quiz_id, data)


@router.delete(
    "/{quiz_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a quiz by ID",
)
async def delete_quiz(quiz_id: int, db: DbSession):
    service = QuizService(db)
    await service.delete_quiz(quiz_id)