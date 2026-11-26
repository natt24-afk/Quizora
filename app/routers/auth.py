from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import (
    DbSession,
    CurrentUser,
    get_session_cookie,
    verify_api_key,
)
from app.repositories.session_repository import SessionRepository
from app.schemas.auth import (
    TokenResponse,
    UserRegisterRequest,
    SessionResponse,
)
from app.schemas.common import MessageResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication & Security"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
)
async def register(data: UserRegisterRequest, db: DbSession):
    """Register a new student, teacher, or admin account."""
    service = AuthService(db)
    return await service.register_user(data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="OAuth2 Login with JWT & Cookie Session",
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    response: Response,
    db: DbSession,
):
    """
    Standard OAuth2 password flow.
    Returns JWT access token AND sets an HTTP-only session cookie (Req #19, #20, #21, #23, #24).
    """
    service = AuthService(db)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    token_response, session_token = await service.authenticate_user(
        username=form_data.username,
        password=form_data.password,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    # Set HTTP-only Cookie (Requirement #23)
    response.set_cookie(
        key="quizora_session",
        value=session_token,
        httponly=True,
        max_age=1800,  # 30 minutes
        samesite="lax",
    )

    return token_response


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout and revoke active session",
)
async def logout(
    response: Response,
    db: DbSession,
    session_cookie: Annotated[Optional[str], Depends(get_session_cookie)],
):
    """Revokes database session and deletes browser cookie (Req #23 & #24)."""
    service = AuthService(db)
    await service.logout_session(session_cookie)
    response.delete_cookie("quizora_session")
    return MessageResponse(message="Successfully logged out and session revoked")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile (JWT Protected)",
)
async def get_my_profile(current_user: CurrentUser):
    """
    Protected endpoint: requires valid Bearer Token (Req #6 & #25).
    """
    return current_user


@router.get(
    "/session-info",
    response_model=Optional[SessionResponse],
    summary="Retrieve session info from Cookie",
)
async def get_session_info(
    db: DbSession,
    session_cookie: Annotated[Optional[str], Depends(get_session_cookie)],
):
    """
    Retrieves active session details using the HTTP cookie (Req #23 & #24).
    """
    if not session_cookie:
        return None
    repo = SessionRepository(db)
    return await repo.get_by_token(session_cookie)


@router.get(
    "/system-status",
    response_model=MessageResponse,
    summary="System Maintenance Info (API-Key Protected)",
)
async def get_system_status(
    api_key: Annotated[str, Depends(verify_api_key)],
):
    """
    Separate operation protected by X-API-Key header (Req #6 & #22).
    """
    return MessageResponse(
        message="System operational",
        detail="Authorized via X-API-Key header",
    )