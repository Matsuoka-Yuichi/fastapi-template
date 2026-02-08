import random
from datetime import datetime

from workers.celery_app import celery_app


@celery_app.task
def print_random_number() -> None:
    """Print a random number generated at the current time."""
    number = random.randint(1, 1000)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"~~ {number} generated at {timestamp} ~~")


# Configure periodic task schedule
celery_app.conf.beat_schedule = {
    "print-random-number-every-30-seconds": {
        "task": "workers.tasks.print_random_number",
        "schedule": 30.0,  # Run every 30 seconds
    },
}
