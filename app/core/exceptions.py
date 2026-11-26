from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Registers centralized, standard exception handlers across the application.
    Satisfies Requirement #15 & Section 14 (Consistent JSON Responses).
    """

    # 1. Standard HTTP Exceptions (400, 401, 403, 404, 409)
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "status_code": exc.status_code,
                "error": exc.detail if isinstance(exc.detail, str) else "HTTP Error",
                "path": request.url.path,
            },
        )

    # 2. Pydantic Request Validation Errors (422 Unprocessable Entity)
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        # Format validation errors into clean, readable field messages
        formatted_errors = []
        for err in exc.errors():
            field = " -> ".join([str(loc) for loc in err.get("loc", []) if loc != "body"])
            formatted_errors.append({
                "field": field or "body",
                "message": err.get("msg", "Invalid input"),
            })

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "error": "Validation Error",
                "details": formatted_errors,
                "path": request.url.path,
            },
        )

    # 3. Database Integrity Errors (Foreign key violations, duplicate keys)
    @app.exception_handler(IntegrityError)
    async def integrity_exception_handler(request: Request, exc: IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "status_code": status.HTTP_409_CONFLICT,
                "error": "Database Conflict",
                "detail": "The operation conflicted with an existing record or foreign key constraint.",
                "path": request.url.path,
            },
        )

    # 4. Fallback Catch-all for Unhandled Exceptions (500 Internal Server Error)
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Prevents leaking internal stack traces or database connection strings
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred. Please contact the administrator.",
                "path": request.url.path,
            },
        )