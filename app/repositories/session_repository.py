from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserSession


class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        user_id: int,
        session_token: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> UserSession:
        """Records an active user session in the database."""
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_by_token(self, session_token: str) -> Optional[UserSession]:
        """Fetch session by token and verify it has not expired."""
        result = await self.db.execute(
            select(UserSession).where(UserSession.session_token == session_token)
        )
        session = result.scalars().first()
        if session:
            expires = session.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)

            if expires < datetime.now(timezone.utc):
                # Session expired: clean it up
                await self.delete_session(session_token)
                return None
        return session

    async def get_user_sessions(self, user_id: int) -> List[UserSession]:
        """Fetch all active sessions for a user."""
        result = await self.db.execute(
            select(UserSession)
            .where(UserSession.user_id == user_id)
            .order_by(UserSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_session(self, session_token: str) -> None:
        """Revoke a specific session (used on logout)."""
        await self.db.execute(
            delete(UserSession).where(UserSession.session_token == session_token)
        )
        await self.db.commit()
