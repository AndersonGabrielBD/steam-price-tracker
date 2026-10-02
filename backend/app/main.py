import asyncio
import contextlib

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.pubsub import listen_for_price_updates
from app.routers import games
from app.websocket_manager import manager

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games.router)


@app.get("/health")
def health():
    return {"status": "ok"}


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
