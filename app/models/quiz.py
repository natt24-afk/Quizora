from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    creator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    time_limit_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    passing_score: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="quizzes")
    creator: Mapped["User"] = relationship("User", back_populates="created_quizzes")
    questions: Mapped[List["Question"]] = relationship(
        "Question", back_populates="quiz", cascade="all, delete-orphan"
    )
    attempts: Mapped[List["QuizAttempt"]] = relationship(
        "QuizAttempt", back_populates="quiz", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    quiz_id: Mapped[int] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), default="multiple_choice", nullable=False)
    points: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    order_num: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="questions")
    choices: Mapped[List["Choice"]] = relationship(
        "Choice", back_populates="question", cascade="all, delete-orphan"
    )
    student_answers: Mapped[List["StudentAnswer"]] = relationship(
        "StudentAnswer", back_populates="question", cascade="all, delete-orphan"
    )


class Choice(Base):
    __tablename__ = "choices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    choice_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationship
    question: Mapped["Question"] = relationship("Question", back_populates="choices")