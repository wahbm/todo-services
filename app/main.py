from contextlib import asynccontextmanager
import os

from fastapi import FastAPI

from app.database import init_database
from app.routes.todos import router as todos_router
from app.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield


app = FastAPI(
    title="Todo API Service",
    description="A SQLite-backed Todo API with CRUD, common todo operations, and Swagger documentation.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    root_path=os.getenv("ROOT_PATH", "").rstrip("/"),
    lifespan=lifespan,
)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["system"],
    summary="Health check",
    description="Return service health status.",
)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


app.include_router(todos_router)
