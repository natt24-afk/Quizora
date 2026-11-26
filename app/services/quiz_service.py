import math
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import Quiz
from app.repositories.category_repository import CategoryRepository
from app.repositories.quiz_repository import QuizRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.quiz import QuizCreate, QuizUpdate, QuizResponse


class QuizService:
    def __init__(self, db: AsyncSession):
        self.repository = QuizRepository(db)
        self.category_repo = CategoryRepository(db)
        self.user_repo = UserRepository(db)

    async def create_quiz(self, data: QuizCreate) -> Quiz:
        """Create a quiz after verifying category and creator exist."""
        # Validate Category existence
        if not await self.category_repo.get_by_id(data.category_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {data.category_id} not found.",
            )

        # Validate Creator existence
        if not await self.user_repo.get_by_id(data.creator_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Creator with User ID {data.creator_id} not found.",
            )

        return await self.repository.create(data)

    async def get_quiz_by_id(self, quiz_id: int) -> Quiz:
        """Fetch a quiz by ID or raise 404."""
        quiz = await self.repository.get_by_id(quiz_id)
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz with ID {quiz_id} not found.",
            )
        return quiz

    async def get_quizzes(
        self,
        page: int = 1,
        size: int = 20,
        category_id: Optional[int] = None,
        is_published: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> PaginatedResponse[QuizResponse]:
        """Fetch paginated quizzes with optional category filtering and title search."""
        skip = (page - 1) * size
        items, total = await self.repository.get_all(
            skip=skip,
            limit=size,
            category_id=category_id,
            is_published=is_published,
            search=search,
        )
        total_pages = math.ceil(total / size) if size > 0 else 0

        return PaginatedResponse[QuizResponse](
            items=[QuizResponse.model_validate(q) for q in items],
            total=total,
            page=page,
            size=size,
            pages=total_pages,
        )

    async def update_quiz(self, quiz_id: int, data: QuizUpdate) -> Quiz:
        """Update quiz fields with foreign key checks."""
        quiz = await self.get_quiz_by_id(quiz_id)

        # Validate new category if provided
        if data.category_id and data.category_id != quiz.category_id:
            if not await self.category_repo.get_by_id(data.category_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with ID {data.category_id} not found.",
                )

        return await self.repository.update(quiz, data)

    async def delete_quiz(self, quiz_id: int) -> None:
        """Delete quiz or raise 404."""
        quiz = await self.get_quiz_by_id(quiz_id)
        await self.repository.delete(quiz)