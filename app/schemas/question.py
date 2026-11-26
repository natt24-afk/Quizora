from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# Choice Schemas
class ChoiceBase(BaseModel):
    choice_text: str = Field(..., min_length=1, description="Text for this answer choice")
    is_correct: bool = Field(False, description="Whether this choice is the correct answer")


class ChoiceCreate(ChoiceBase):
    pass


class ChoiceResponse(ChoiceBase):
    id: int
    question_id: int

    model_config = ConfigDict(from_attributes=True)


# Question Schemas
class QuestionBase(BaseModel):
    question_text: str = Field(..., min_length=3, description="Question text/prompt")
    question_type: str = Field("multiple_choice", description="Question type")
    points: float = Field(1.0, ge=0.5, le=100.0, description="Points awarded for correct answer")
    order_num: int = Field(1, ge=1, description="Display order number")


class QuestionCreate(QuestionBase):
    quiz_id: int = Field(..., description="ID of the parent quiz")
    choices: List[ChoiceCreate] = Field(
        ..., min_length=2, description="At least two choices are required"
    )


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = Field(None, min_length=3)
    question_type: Optional[str] = None
    points: Optional[float] = Field(None, ge=0.5, le=100.0)
    order_num: Optional[int] = Field(None, ge=1)


class QuestionResponse(QuestionBase):
    id: int
    quiz_id: int
    created_at: datetime
    choices: List[ChoiceResponse] = []

    model_config = ConfigDict(from_attributes=True)