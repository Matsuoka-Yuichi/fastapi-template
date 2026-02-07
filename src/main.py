from fastapi import FastAPI

from features.tasks.api import router as tasks_router

app = FastAPI()


app.include_router(tasks_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello from fastapi-template!"}
