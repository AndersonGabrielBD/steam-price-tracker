"""Bridges the Celery worker process (publisher) and the FastAPI process
(subscriber) via a Redis pub/sub channel, so a price change picked up by a
background task can be pushed live to connected WebSocket clients.
"""

import json

import redis
import redis.asyncio as aioredis
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

PRICE_UPDATES_CHANNEL = "price_updates"

_sync_redis = redis.from_url(settings.redis_url)


def publish_price_update(event: dict) -> None:
    """Called from the Celery task (sync context) when a price changes."""
    _sync_redis.publish(PRICE_UPDATES_CHANNEL, json.dumps(event, default=str))
    logger.info("price_update_published", game_id=event.get("game_id"))


async def listen_for_price_updates():
    """Async generator yielding each price-update event. Used by the FastAPI
    app's startup background task to relay events to WebSocket clients.
    """
    client = aioredis.from_url(settings.redis_url)
    pubsub = client.pubsub()
    await pubsub.subscribe(PRICE_UPDATES_CHANNEL)
    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            yield json.loads(message["data"])
    finally:
        await pubsub.unsubscribe(PRICE_UPDATES_CHANNEL)
        await client.close()
