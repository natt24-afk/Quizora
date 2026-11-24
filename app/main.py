
from fastapi import FastAPI

app = FastAPI(
    title="Quizora App API",
    description="Backend API for the Quiz App Integrative Programming Project",
    version="1.0.0",
)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Quizora App API",
        "status": "running",
        "project": "Quizora App",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "application": "Quizora App API",
    }
