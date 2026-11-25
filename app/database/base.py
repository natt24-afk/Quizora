from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    All models will inherit from this class to register with SQLAlchemy metadata.
    """
    pass