from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import Quiz
from app.schemas.quiz import QuizCreate, QuizUpdate


class QuizRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, quiz_id: int) -> Optional[Quiz]:
        result = await self.db.execute(select(Quiz).where(Quiz.id == quiz_id))
        return result.scalars().first()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        category_id: Optional[int] = None,
        is_published: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> tuple[List[Quiz], int]:
        query = select(Quiz)
        count_query = select(func.count(Quiz.id))

        if category_id is not None:
            query = query.where(Quiz.category_id == category_id)
            count_query = count_query.where(Quiz.category_id == category_id)

        if is_published is not None:
            query = query.where(Quiz.is_published == is_published)
            count_query = count_query.where(Quiz.is_published == is_published)

        if search:
            search_filter = Quiz.title.ilike(f"%{search}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        result = await self.db.execute(
            query.order_by(Quiz.id.desc()).offset(skip).limit(limit)
        )
        items = list(result.scalars().all())
        return items, total

    async def create(self, data: QuizCreate) -> Quiz:
        quiz = Quiz(
            title=data.title,
            description=data.description,
            category_id=data.category_id,
            creator_id=data.creator_id,
            time_limit_minutes=data.time_limit_minutes,
            passing_score=data.passing_score,
            is_published=data.is_published,
        )
        self.db.add(quiz)
        await self.db.commit()
        await self.db.refresh(quiz)
        return quiz

    async def update(self, quiz: Quiz, data: QuizUpdate) -> Quiz:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(quiz, key, value)

        await self.db.commit()
        await self.db.refresh(quiz)
        return quiz

    async def delete(self, quiz: Quiz) -> None:
        await self.db.delete(quiz)
        await self.db.commit()