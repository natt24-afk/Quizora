from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.attempt import AttemptStatus


# 1. Student-Safe Schemas (Hides `is_correct` so students cannot inspect HTML/JSON to cheat)
class ChoiceStudentView(BaseModel):
    id: int
    question_id: int
    choice_text: str

    model_config = ConfigDict(from_attributes=True)


class QuestionStudentView(BaseModel):
    id: int
    quiz_id: int
    question_text: str
    question_type: str
    points: float
    order_num: int
    choices: List[ChoiceStudentView]

    model_config = ConfigDict(from_attributes=True)


# 2. Starting an Attempt
class AttemptStartRequest(BaseModel):
    quiz_id: int = Field(..., description="ID of the quiz to take")
    user_id: int = Field(..., description="ID of the student taking the quiz")


class AttemptStartResponse(BaseModel):
    attempt_id: int
    quiz_id: int
    quiz_title: str
    time_limit_minutes: int
    total_questions: int
    started_at: datetime
    questions: List[QuestionStudentView]


# 3. Submitting Answers
class AnswerSubmissionItem(BaseModel):
    question_id: int = Field(..., description="ID of the question answered")
    chosen_choice_id: Optional[int] = Field(None, description="ID of the selected choice (None if skipped)")


class QuizSubmissionRequest(BaseModel):
    answers: List[AnswerSubmissionItem] = Field(..., description="List of submitted answers")


# 4. Result and Scorecard Schemas (Returned after submission)
class AnswerResultDetail(BaseModel):
    question_id: int
    question_text: str
    chosen_choice_id: Optional[int]
    correct_choice_id: Optional[int]
    is_correct: bool
    points_awarded: float
    max_points: float


class AttemptResultResponse(BaseModel):
    id: int
    quiz_id: int
    user_id: int
    score: float
    max_possible_score: float
    percentage: float
    is_passed: bool
    status: AttemptStatus
    started_at: datetime
    completed_at: Optional[datetime]
    answers: List[AnswerResultDetail] = []

    model_config = ConfigDict(from_attributes=True)


class AttemptSummaryResponse(BaseModel):
    id: int
    quiz_id: int
    user_id: int
    score: float
    max_possible_score: float
    percentage: float
    is_passed: bool
    status: AttemptStatus
    started_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)