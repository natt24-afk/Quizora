from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db

# Modern FastAPI Type Alias for Dependency Injection
# In any router endpoint, typing `db: DbSession` automatically injects
# an active asynchronous MariaDB session and safely closes it when done.
DbSession = Annotated[AsyncSession, Depends(get_db)]