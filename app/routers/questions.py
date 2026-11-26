from typing import List
from fastapi import APIRouter, status

from app.core.dependencies import DbSession, RequireTeacherOrAdmin
from app.schemas.question import QuestionCreate, QuestionUpdate, QuestionResponse
from app.services.question_service import QuestionService

router = APIRouter(prefix="/questions", tags=["Questions"])


@router.post(
    "/",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a question with choices (Teacher/Admin only)",
)
async def create_question(
    data: QuestionCreate,
    db: DbSession,
    current_user: RequireTeacherOrAdmin,
):
    service = QuestionService(db)
    return await service.create_question(data)


@router.get(
    "/quiz/{quiz_id}",
    response_model=List[QuestionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all questions for a specific quiz",
)
async def get_quiz_questions(quiz_id: int, db: DbSession):
    service = QuestionService(db)
    return await service.get_questions_by_quiz_id(quiz_id)


@router.get(
    "/{question_id}",
    response_model=QuestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a question by ID",
)
async def get_question(question_id: int, db: DbSession):
    service = QuestionService(db)
    return await service.get_question_by_id(question_id)


@router.put(
    "/{question_id}",
    response_model=QuestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a question by ID (Teacher/Admin only)",
)
async def update_question(
    question_id: int,
    data: QuestionUpdate,
    db: DbSession,
    current_user: RequireTeacherOrAdmin,
):
    service = QuestionService(db)
    return await service.update_question(question_id, data)


@router.delete(
    "/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a question by ID (Teacher/Admin only)",
)
async def delete_question(
    question_id: int,
    db: DbSession,
    current_user: RequireTeacherOrAdmin,
):
    service = QuestionService(db)
    await service.delete_question(question_id)