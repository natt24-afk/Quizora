from typing import Generic, List, TypeVar, Optional
from pydantic import BaseModel, ConfigDict, Field

# Generic type variable for paginated data
T = TypeVar("T")


class BaseSchema(BaseModel):
    """
    Root base schema configured to read from SQLAlchemy ORM models directly.
    """
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """
    Standard response schema for simple messages, actions, or status returns.
    """
    message: str
    detail: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standard generic pagination wrapper.
    Ensures every paginated list returned by the API has identical structure.
    """
    items: List[T]
    total: int = Field(..., description="Total number of items matching query")
    page: int = Field(..., ge=1, description="Current page number")
    size: int = Field(..., ge=1, description="Number of items per page")
    pages: int = Field(..., ge=0, description="Total number of pages available")