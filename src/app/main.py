from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.features.tasks.api import router as tasks_router
from shared.infra import db, settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events."""
    # Startup: initialize async database pool
    if settings.database_url:
        await db.initialize_async_pool()
    yield
    # Shutdown: close async database pool
    if settings.database_url:
        await db.close_async_pool()


app = FastAPI(
    title="fastapi-template",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.client_url] if settings.client_url else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Hello from fastapi-template!",
        "environment": settings.environment,
    }
