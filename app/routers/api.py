from fastapi import APIRouter
from app.schemas.common import MessageResponse
from app.routers import categories, quizzes, users, questions

# Central API Router with API versioning prefix
api_router = APIRouter(prefix="/api/v1")


@api_router.get(
    "/ping",
    response_model=MessageResponse,
    summary="API v1 Health Ping",
    tags=["System"],
)
async def api_ping():
    """
    Test endpoint verifying the modular /api/v1 router is active.
    """
    return MessageResponse(
        message="Quizora API v1 is operational",
        detail="Backend modular architecture active",
    )

# Mount Module Routers
api_router.include_router(categories.router)
api_router.include_router(users.router)
api_router.include_router(quizzes.router)
api_router.include_router(questions.router)
