from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import Question
from app.repositories.question_repository import QuestionRepository
from app.repositories.quiz_repository import QuizRepository
from app.schemas.question import QuestionCreate, QuestionUpdate


class QuestionService:
    def __init__(self, db: AsyncSession):
        self.repository = QuestionRepository(db)
        self.quiz_repo = QuizRepository(db)

    async def create_question(self, data: QuestionCreate) -> Question:
        """Create question with choices after validation."""
        # 1. Verify parent quiz exists
        if not await self.quiz_repo.get_by_id(data.quiz_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz with ID {data.quiz_id} not found.",
            )

        # 2. Business rule: At least one choice must be marked as correct
        has_correct = any(c.is_correct for c in data.choices)
        if not has_correct:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one choice must be marked as correct (is_correct=True).",
            )

        return await self.repository.create_with_choices(data)

    async def get_question_by_id(self, question_id: int) -> Question:
        """Fetch question or raise 404."""
        question = await self.repository.get_by_id(question_id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question with ID {question_id} not found.",
            )
        return question

    async def get_questions_by_quiz_id(self, quiz_id: int) -> List[Question]:
        """Fetch all questions for a quiz."""
        if not await self.quiz_repo.get_by_id(quiz_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz with ID {quiz_id} not found.",
            )
        return await self.repository.get_by_quiz_id(quiz_id)

    async def update_question(self, question_id: int, data: QuestionUpdate) -> Question:
        """Update question fields."""
        question = await self.get_question_by_id(question_id)
        return await self.repository.update(question, data)

    async def delete_question(self, question_id: int) -> None:
        """Delete question or raise 404."""
        question = await self.get_question_by_id(question_id)
        await self.repository.delete(question)