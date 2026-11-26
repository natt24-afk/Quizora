import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import setup_exception_handlers
from app.database.connection import engine
from app.routers import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Executes startup and shutdown tasks asynchronously.
    """
    print(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode...")
    yield
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

# 1. Custom HTTP Middleware: Latency & Performance Header 
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Measures endpoint execution duration and appends X-Process-Time header."""
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response


# 2. CORS Middleware (for Android emulators, devices, and web clients)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time"],
)

# 3. Register Centralized Exception Handlers 
setup_exception_handlers(app)

# 4. Mount the Versioned Modular API Router (/api/v1)
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