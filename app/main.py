from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database.connection import engine
from app.routers import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Executes startup and shutdown tasks asynchronously.
    """
    # Startup: Can log startup or verify database connectivity
    print(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode...")
    yield
    # Shutdown: Safely dispose the async database connection pool
    print(f"Shutting down {settings.APP_NAME} database engine...")
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="Quiz App Integrative Programming Project - Database-driven RESTful API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS (Cross-Origin Resource Sharing) Middleware
# Required so Android emulators, physical devices, or web clients can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the modular API router (all versioned endpoints live under /api/v1)
app.include_router(api_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "project": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "docs": "/docs",
        "api_v1": "/api/v1/ping",
        "status": "running",
    }


@app.get("/health", tags=["Root"])
async def health_check():
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
    }