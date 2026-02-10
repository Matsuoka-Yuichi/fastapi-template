from typing import Any

from celery import Celery
from celery.signals import worker_process_shutdown

from shared.infra import db, settings

# Create Celery app instance
celery_app = Celery(
    "fastapi-template",
    broker=settings.redis_url or "redis://localhost:6379/0",
    backend=settings.redis_url or "redis://localhost:6379/0",
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)


@worker_process_shutdown.connect
def close_db_pool(sender: Any, **kwargs: Any) -> None:
    """Close database pool when worker process shuts down.
    
    Note: We don't initialize the pool here - it's created lazily
    when sync_connection() is first called in a task (after fork).
    """
    if settings.database_url:
        db.close_sync_pool()


# Import tasks to register them with Celery
from workers import tasks  # noqa: E402, F401
