from fastapi import APIRouter, Query, status

from app.core.dependencies import DbSession
from app.schemas.attempt import (
    AttemptStartRequest,
    AttemptStartResponse,
    QuizSubmissionRequest,
    AttemptResultResponse,
    AttemptSummaryResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.attempt_service import AttemptService

router = APIRouter(prefix="/attempts", tags=["Quiz Attempts"])


@router.post(
    "/start",
    response_model=AttemptStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a quiz attempt",
)
async def start_quiz_attempt(data: AttemptStartRequest, db: DbSession):
    service = AttemptService(db)
    return await service.start_attempt(data)


@router.post(
    "/{attempt_id}/submit",
    response_model=AttemptResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit answers and receive instant scorecard",
)
async def submit_quiz_attempt(
    attempt_id: int, data: QuizSubmissionRequest, db: DbSession
):
    service = AttemptService(db)
    return await service.submit_attempt(attempt_id, data)


@router.get(
    "/{attempt_id}",
    response_model=AttemptResultResponse,
    status_code=status.HTTP_200_OK,
    summary="View attempt results and question breakdown",
)
async def get_attempt_result(attempt_id: int, db: DbSession):
    service = AttemptService(db)
    return await service.get_attempt_result(attempt_id)


@router.get(
    "/user/{user_id}",
    response_model=PaginatedResponse[AttemptSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="View student quiz attempt history",
)
async def get_user_attempt_history(
    user_id: int,
    db: DbSession,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    service = AttemptService(db)
    return await service.get_user_history(user_id=user_id, page=page, size=size)