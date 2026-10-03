from celery import Celery

from app.config import settings
from app.logging_config import configure_logging

configure_logging()

celery_app = Celery(
    "price_tracker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    "check-all-game-prices": {
        "task": "app.tasks.check_all_game_prices",
        "schedule": settings.price_check_interval_minutes * 60,
    },
}
