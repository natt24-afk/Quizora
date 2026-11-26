from typing import Annotated, List, Optional
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_access_token
from app.database.connection import get_db
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

# 1. Database Session Injection
DbSession = Annotated[AsyncSession, Depends(get_db)]

# 2. OAuth2 Password Bearer for Swagger UI Authorization (Req #20 & #21)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    description="JWT Bearer token authentication",
)

# 3. API Key Header for separate administrative operation (Req #22)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# 4. Get Current User via Bearer Token (Req #19 & #21)
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession,
) -> User:
    """Decodes JWT, retrieves user from database, and verifies active status."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str: Optional[str] = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user account"
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


# 5. Role-Based Access Control (RBAC) Dependency Factory (Req #3 & #25)
def require_roles(allowed_roles: List[UserRole]):
    """
    Dependency factory that restricts endpoint access to specified roles.
    Raises 403 Forbidden if user's role is not authorized.
    """
    async def role_checker(current_user: CurrentUser) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of {[r.value for r in allowed_roles]} roles",
            )
        return current_user

    return role_checker


# Convenient Role Shortcuts
RequireTeacherOrAdmin = Annotated[
    User, Depends(require_roles([UserRole.ADMIN, UserRole.TEACHER]))
]
RequireAdmin = Annotated[User, Depends(require_roles([UserRole.ADMIN]))]


# 6. Cookie Retrieval Dependency (Req #23)
def get_session_cookie(request: Request) -> Optional[str]:
    """Retrieves session token stored in browser HTTP cookie."""
    return request.cookies.get("quizora_session")


# 7. API Key Verification Dependency (Req #22)
async def verify_api_key(
    api_key: Annotated[Optional[str], Security(api_key_header)]
) -> str:
    """
    Validates X-API-Key header for protected system/maintenance operations.
    """
    if not api_key or api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing X-API-Key header",
        )
    return api_key