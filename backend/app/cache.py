"""Thin Redis read-through cache, used to avoid hitting the Steam API on
every request/check within a short window (default: shorter than the Celery
price-check interval, so cached data never masks a real scheduled check).
"""

import json
from collections.abc import Callable
from typing import TypeVar

import redis

from app.config import settings

_redis_client = redis.from_url(settings.redis_url, decode_responses=True)

T = TypeVar("T")


def get_redis_client() -> redis.Redis:
    return _redis_client


def cached(key: str, loader: Callable[[], T], ttl_seconds: int | None = None) -> T:
    """Returns the cached value for `key` if present, otherwise calls `loader()`,
    caches the result, and returns it. `loader`'s return value must be JSON-serializable.

    Redis is a performance optimization here, not a correctness dependency: if it's
    unreachable, we silently fall back to calling `loader()` directly instead of
    failing the whole request.
    """
    try:
        raw = _redis_client.get(key)
    except redis.RedisError:
        return loader()

    if raw is not None:
        return json.loads(raw)

    value = loader()
    try:
        _redis_client.set(key, json.dumps(value), ex=ttl_seconds or settings.price_cache_ttl_seconds)
    except redis.RedisError:
        pass
    return value
