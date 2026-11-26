from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attempt import QuizAttempt, StudentAnswer, AttemptStatus


class AttemptRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_attempt(self, quiz_id: int, user_id: int) -> QuizAttempt:
        """Create a new attempt in IN_PROGRESS status."""
        attempt = QuizAttempt(
            quiz_id=quiz_id,
            user_id=user_id,
            status=AttemptStatus.IN_PROGRESS,
            score=0.0,
            max_possible_score=0.0,
            percentage=0.0,
            is_passed=False,
        )
        self.db.add(attempt)
        await self.db.commit()
        await self.db.refresh(attempt)
        return attempt

    async def get_by_id(self, attempt_id: int) -> Optional[QuizAttempt]:
        """Fetch attempt with its answers eagerly loaded."""
        result = await self.db.execute(
            select(QuizAttempt)
            .options(selectinload(QuizAttempt.answers))
            .where(QuizAttempt.id == attempt_id)
        )
        return result.scalars().first()

    async def get_by_user_id(
        self, user_id: int, skip: int = 0, limit: int = 20
    ) -> tuple[List[QuizAttempt], int]:
        """Get paginated attempts for a specific student."""
        count_res = await self.db.execute(
            select(func.count(QuizAttempt.id)).where(QuizAttempt.user_id == user_id)
        )
        total = count_res.scalar() or 0

        result = await self.db.execute(
            select(QuizAttempt)
            .where(QuizAttempt.user_id == user_id)
            .order_by(QuizAttempt.started_at.desc())
            .offset(skip)
            .limit(limit)
        )
        items = list(result.scalars().all())
        return items, total

    async def get_by_quiz_id(
        self, quiz_id: int, skip: int = 0, limit: int = 20
    ) -> tuple[List[QuizAttempt], int]:
        """Get paginated attempts for a specific quiz (for teachers/admins)."""
        count_res = await self.db.execute(
            select(func.count(QuizAttempt.id)).where(QuizAttempt.quiz_id == quiz_id)
        )
        total = count_res.scalar() or 0

        result = await self.db.execute(
            select(QuizAttempt)
            .where(QuizAttempt.quiz_id == quiz_id)
            .order_by(QuizAttempt.started_at.desc())
            .offset(skip)
            .limit(limit)
        )
        items = list(result.scalars().all())
        return items, total

    async def record_submission_transaction(
        self,
        attempt: QuizAttempt,
        calculated_score: float,
        max_score: float,
        percentage: float,
        is_passed: bool,
        evaluated_answers: List[Dict[str, Any]],
    ) -> QuizAttempt:
        """
        ATOMIC DATABASE TRANSACTION (Requirement #9):
        Records all student answer items and updates the attempt status
        to COMPLETED together. If any insert fails, the transaction rolls back.
        """
        # 1. Insert each individual student answer
        for item in evaluated_answers:
            ans = StudentAnswer(
                attempt_id=attempt.id,
                question_id=item["question_id"],
                chosen_choice_id=item["chosen_choice_id"],
                is_correct=item["is_correct"],
                points_awarded=item["points_awarded"],
            )
            self.db.add(ans)

        # 2. Update the parent attempt record
        attempt.score = calculated_score
        attempt.max_possible_score = max_score
        attempt.percentage = percentage
        attempt.is_passed = is_passed
        attempt.status = AttemptStatus.COMPLETED
        attempt.completed_at = datetime.now(timezone.utc)

        # 3. Commit atomically
        await self.db.commit()
        await self.db.refresh(attempt)
        return await self.get_by_id(attempt.id)