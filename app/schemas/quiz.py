from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class QuizBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=150, description="Quiz title")
    description: Optional[str] = Field(None, max_length=1000, description="Quiz description")
    category_id: int = Field(..., description="ID of the category")
    time_limit_minutes: int = Field(30, ge=1, le=300, description="Time limit in minutes")
    passing_score: float = Field(70.0, ge=0.0, le=100.0, description="Passing score percentage")
    is_published: bool = Field(False, description="Whether the quiz is visible to students")


class QuizCreate(QuizBase):
    creator_id: int = Field(..., description="ID of the user creating the quiz")


class QuizUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=150)
    description: Optional[str] = None
    category_id: Optional[int] = None
    time_limit_minutes: Optional[int] = Field(None, ge=1, le=300)
    passing_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    is_published: Optional[bool] = None


class QuizResponse(QuizBase):
    id: int
    creator_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)