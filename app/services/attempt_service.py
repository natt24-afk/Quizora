import math
from typing import List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attempt import AttemptStatus
from app.repositories.attempt_repository import AttemptRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.quiz_repository import QuizRepository
from app.repositories.user_repository import UserRepository
from app.schemas.attempt import (
    AttemptStartRequest,
    AttemptStartResponse,
    ChoiceStudentView,
    QuestionStudentView,
    QuizSubmissionRequest,
    AttemptResultResponse,
    AnswerResultDetail,
    AttemptSummaryResponse,
)
from app.schemas.common import PaginatedResponse


class AttemptService:
    def __init__(self, db: AsyncSession):
        self.repository = AttemptRepository(db)
        self.quiz_repo = QuizRepository(db)
        self.user_repo = UserRepository(db)
        self.question_repo = QuestionRepository(db)

    async def start_attempt(self, data: AttemptStartRequest) -> AttemptStartResponse:
        """Starts a new attempt and returns questions without answer leaks."""
        # 1. Verify user exists
        user = await self.user_repo.get_by_id(data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {data.user_id} not found.",
            )

        # 2. Verify quiz exists and is published
        quiz = await self.quiz_repo.get_by_id(data.quiz_id)
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz with ID {data.quiz_id} not found.",
            )
        if not quiz.is_published:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This quiz is not currently available for attempts.",
            )

        # 3. Retrieve questions
        questions = await self.question_repo.get_by_quiz_id(data.quiz_id)
        if not questions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This quiz does not have any questions yet.",
            )

        # 4. Create attempt record
        attempt = await self.repository.create_attempt(
            quiz_id=data.quiz_id, user_id=data.user_id
        )

        # 5. Build student view (clean choices with NO is_correct flag)
        student_questions: List[QuestionStudentView] = []
        for q in questions:
            student_choices = [
                ChoiceStudentView(id=c.id, question_id=c.question_id, choice_text=c.choice_text)
                for c in q.choices
            ]
            student_questions.append(
                QuestionStudentView(
                    id=q.id,
                    quiz_id=q.quiz_id,
                    question_text=q.question_text,
                    question_type=q.question_type,
                    points=q.points,
                    order_num=q.order_num,
                    choices=student_choices,
                )
            )

        return AttemptStartResponse(
            attempt_id=attempt.id,
            quiz_id=quiz.id,
            quiz_title=quiz.title,
            time_limit_minutes=quiz.time_limit_minutes,
            total_questions=len(student_questions),
            started_at=attempt.started_at,
            questions=student_questions,
        )

    async def submit_attempt(
        self, attempt_id: int, data: QuizSubmissionRequest
    ) -> AttemptResultResponse:
        """Evaluates student answers, scores the quiz, and commits the result."""
        # 1. Fetch attempt
        attempt = await self.repository.get_by_id(attempt_id)
        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attempt with ID {attempt_id} not found.",
            )

        # 2. Prevent double submission
        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This quiz attempt has already been submitted and completed.",
            )

        # 3. Fetch Quiz and true Question/Choice data
        quiz = await self.quiz_repo.get_by_id(attempt.quiz_id)
        questions = await self.question_repo.get_by_quiz_id(attempt.quiz_id)

        # Index submitted answers by question_id
        submitted_dict = {ans.question_id: ans.chosen_choice_id for ans in data.answers}

        total_score = 0.0
        max_score = 0.0
        evaluated_items: List[Dict[str, Any]] = []
        result_details: List[AnswerResultDetail] = []

        # 4. Automatic Grading Loop
        for q in questions:
            max_score += q.points
            chosen_id = submitted_dict.get(q.id)

            # Find the true correct choice
            correct_choice = next((c for c in q.choices if c.is_correct), None)
            correct_id = correct_choice.id if correct_choice else None

            # Check if answer is correct
            is_correct = (chosen_id is not None) and (chosen_id == correct_id)
            awarded = q.points if is_correct else 0.0
            total_score += awarded

            evaluated_items.append({
                "question_id": q.id,
                "chosen_choice_id": chosen_id,
                "is_correct": is_correct,
                "points_awarded": awarded,
            })

            result_details.append(
                AnswerResultDetail(
                    question_id=q.id,
                    question_text=q.question_text,
                    chosen_choice_id=chosen_id,
                    correct_choice_id=correct_id,
                    is_correct=is_correct,
                    points_awarded=awarded,
                    max_points=q.points,
                )
            )

        percentage = round((total_score / max_score) * 100, 2) if max_score > 0 else 0.0
        is_passed = percentage >= quiz.passing_score

        # 5. Atomic database transaction
        saved_attempt = await self.repository.record_submission_transaction(
            attempt=attempt,
            calculated_score=total_score,
            max_score=max_score,
            percentage=percentage,
            is_passed=is_passed,
            evaluated_answers=evaluated_items,
        )

        return AttemptResultResponse(
            id=saved_attempt.id,
            quiz_id=saved_attempt.quiz_id,
            user_id=saved_attempt.user_id,
            score=saved_attempt.score,
            max_possible_score=saved_attempt.max_possible_score,
            percentage=saved_attempt.percentage,
            is_passed=saved_attempt.is_passed,
            status=saved_attempt.status,
            started_at=saved_attempt.started_at,
            completed_at=saved_attempt.completed_at,
            answers=result_details,
        )

    async def get_attempt_result(self, attempt_id: int) -> AttemptResultResponse:
        """Fetch result scorecard of an attempt."""
        attempt = await self.repository.get_by_id(attempt_id)
        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attempt with ID {attempt_id} not found.",
            )

        questions = await self.question_repo.get_by_quiz_id(attempt.quiz_id)
        q_map = {q.id: q for q in questions}

        details: List[AnswerResultDetail] = []
        for ans in attempt.answers:
            q = q_map.get(ans.question_id)
            correct_choice = next((c for c in q.choices if c.is_correct), None) if q else None
            details.append(
                AnswerResultDetail(
                    question_id=ans.question_id,
                    question_text=q.question_text if q else "Deleted Question",
                    chosen_choice_id=ans.chosen_choice_id,
                    correct_choice_id=correct_choice.id if correct_choice else None,
                    is_correct=ans.is_correct,
                    points_awarded=ans.points_awarded,
                    max_points=q.points if q else ans.points_awarded,
                )
            )

        return AttemptResultResponse(
            id=attempt.id,
            quiz_id=attempt.quiz_id,
            user_id=attempt.user_id,
            score=attempt.score,
            max_possible_score=attempt.max_possible_score,
            percentage=attempt.percentage,
            is_passed=attempt.is_passed,
            status=attempt.status,
            started_at=attempt.started_at,
            completed_at=attempt.completed_at,
            answers=details,
        )

    async def get_user_history(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PaginatedResponse[AttemptSummaryResponse]:
        """Fetch student attempt history."""
        skip = (page - 1) * size
        items, total = await self.repository.get_by_user_id(user_id=user_id, skip=skip, limit=size)
        total_pages = math.ceil(total / size) if size > 0 else 0

        return PaginatedResponse[AttemptSummaryResponse](
            items=[AttemptSummaryResponse.model_validate(a) for a in items],
            total=total,
            page=page,
            size=size,
            pages=total_pages,
        )