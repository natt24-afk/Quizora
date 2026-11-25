from fastapi import APIRouter
from app.schemas.common import MessageResponse

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

