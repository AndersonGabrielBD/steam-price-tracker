import asyncio
import contextlib
import uuid

import redis
import structlog
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text

from app.cache import get_redis_client
from app.config import settings
from app.database import Base, engine
from app.logging_config import configure_logging
from app.pubsub import listen_for_price_updates
from app.rate_limit import limiter
from app.routers import games
from app.websocket_manager import manager

configure_logging()
logger = structlog.get_logger(__name__)

_pubsub_task: asyncio.Task | None = None


async def _relay_price_updates() -> None:
    async for event in listen_for_price_updates():
        await manager.broadcast(event)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Created here (rather than at import time) so importing this module in
    # tests doesn't require a live Postgres connection -- tests build their
    # own schema against a SQLite engine and never trigger this lifespan.
    Base.metadata.create_all(bind=engine)
    global _pubsub_task
    _pubsub_task = asyncio.create_task(_relay_price_updates())
    yield
    if _pubsub_task:
        _pubsub_task.cancel()


app = FastAPI(title="Steam Price Tracker", version="0.1.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games.router)


@app.middleware("http")
async def bind_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(request_id=request_id)
    try:
        return await call_next(request)
    finally:
        structlog.contextvars.clear_contextvars()


@app.get("/health")
def health():
    checks = {"database": "ok", "redis": "ok"}

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        checks["database"] = "error"
        logger.warning("health_check_database_failed", error=str(exc))

    try:
        get_redis_client().ping()
    except redis.RedisError as exc:
        checks["redis"] = "error"
        logger.warning("health_check_redis_failed", error=str(exc))

    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return JSONResponse(
        content={"status": status, "checks": checks},
        status_code=200 if status == "ok" else 503,
    )


@app.websocket("/ws/prices")
async def ws_prices(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # The client doesn't need to send anything; we just keep the
            # connection open and push events from the broadcast side.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
