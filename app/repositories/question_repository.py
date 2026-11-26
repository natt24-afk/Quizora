from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import Question, Choice
from app.schemas.question import QuestionCreate, QuestionUpdate


class QuestionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, question_id: int) -> Optional[Question]:
        """Fetch question by ID eagerly loading its choices."""
        result = await self.db.execute(
            select(Question)
            .options(selectinload(Question.choices))
            .where(Question.id == question_id)
        )
        return result.scalars().first()

    async def get_by_quiz_id(self, quiz_id: int) -> List[Question]:
        """Fetch all questions belonging to a quiz ordered by order_num."""
        result = await self.db.execute(
            select(Question)
            .options(selectinload(Question.choices))
            .where(Question.quiz_id == quiz_id)
            .order_by(Question.order_num.asc())
        )
        return list(result.scalars().all())

    async def create_with_choices(self, data: QuestionCreate) -> Question:
        """Atomic transaction: Create question and all choices together."""
        question = Question(
            quiz_id=data.quiz_id,
            question_text=data.question_text,
            question_type=data.question_type,
            points=data.points,
            order_num=data.order_num,
        )
        self.db.add(question)
        await self.db.flush()  # Flushes to get generated question.id

        # Add choices referencing the new question.id
        for choice_data in data.choices:
            choice = Choice(
                question_id=question.id,
                choice_text=choice_data.choice_text,
                is_correct=choice_data.is_correct,
            )
            self.db.add(choice)

        await self.db.commit()
        return await self.get_by_id(question.id)

    async def update(self, question: Question, data: QuestionUpdate) -> Question:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(question, key, value)

        await self.db.commit()
        await self.db.refresh(question)
        return question

    async def delete(self, question: Question) -> None:
        """Cascade deletes choices automatically."""
        await self.db.delete(question)
        await self.db.commit()