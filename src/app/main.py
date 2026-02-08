from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.features.tasks.api import router as tasks_router
from shared.infra import settings

app = FastAPI(
    title="fastapi-template",
    version="0.1.0",
    debug=settings.debug,
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
