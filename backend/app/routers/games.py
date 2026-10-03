from datetime import datetime
from typing import Literal

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.itad_client import ItadAPIError, fetch_steam_br_history, lookup_game_id
from app.models import Game, PriceSnapshot, utcnow
from app.schemas import GameCreate, GameHistoryOut, GameOut
from app.steam_client import GameNotFoundError, SteamAPIError, fetch_game_price, search_games

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/games", tags=["games"])


def _backfill_history(db: Session, game: Game) -> None:
    """Best-effort: populate `game`'s price_history with real past Steam-BR
    prices from ITAD, so the chart doesn't start empty. Never raises --
    a missing/invalid API key or a flaky ITAD response should never block
    adding a game, it just means no backfill happens this time.
    """
    if not settings.itad_api_key:
        return

    try:
        itad_game_id = lookup_game_id(game.steam_appid)
        if itad_game_id is None:
            return
        points = fetch_steam_br_history(itad_game_id)
    except ItadAPIError as exc:
        logger.warning("itad_backfill_failed", steam_appid=game.steam_appid, error=str(exc))
        return

    for point in points:
        db.add(
            PriceSnapshot(
                game_id=game.id,
                price_brl=point["price_brl"],
                initial_price_brl=point["initial_price_brl"],
                discount_percent=point["discount_percent"],
                is_on_sale=point["is_on_sale"],
                source="itad_backfill",
                price_currency="BRL",
                checked_at=datetime.fromisoformat(point["checked_at"]),
            )
        )
    db.commit()
    logger.info("itad_backfill_done", steam_appid=game.steam_appid, points=len(points))


def _is_all_time_low(db: Session, game_id: int, latest_price_brl) -> bool:
    """True when the latest known price matches the lowest ever recorded --
    i.e. this is the best time anyone has seen to buy it. Requires more than
    one snapshot (a single data point is trivially "the lowest").
    """
    if latest_price_brl is None or float(latest_price_brl) <= 0:
        return False
    count = db.query(func.count(PriceSnapshot.id)).filter(PriceSnapshot.game_id == game_id).scalar()
    if count <= 1:
        return False
    min_price = db.query(func.min(PriceSnapshot.price_brl)).filter(PriceSnapshot.game_id == game_id).scalar()
    return min_price is not None and float(latest_price_brl) <= float(min_price)


def _with_latest_price(db: Session, game: Game) -> GameOut:
    latest = (
        db.query(PriceSnapshot)
        .filter(PriceSnapshot.game_id == game.id)
        .order_by(PriceSnapshot.checked_at.desc())
        .first()
    )
    is_all_time_low = _is_all_time_low(db, game.id, latest.price_brl if latest else None)
    return GameOut.model_validate(
        {**game.__dict__, "latest_price": latest, "is_all_time_low": is_all_time_low}
    )


@router.get("/search")
def search(q: str = Query(min_length=2)):
    """Best-effort search by name, to help pick a Steam appid in the UI."""
    return search_games(q)


_SORT_KEYS = {
    "added_at": lambda g: g.added_at,
    "name": lambda g: g.name.lower(),
    "price": lambda g: float(g.latest_price.price_brl) if g.latest_price else 0.0,
    "discount": lambda g: g.latest_price.discount_percent if g.latest_price else 0,
}


@router.get("", response_model=list[GameOut])
def list_games(
    db: Session = Depends(get_db),
    sort: Literal["added_at", "name", "price", "discount"] = "added_at",
    order: Literal["asc", "desc"] = "desc",
    on_sale_only: bool = False,
):
    games = db.query(Game).all()
    out = [_with_latest_price(db, game) for game in games]

    if on_sale_only:
        out = [g for g in out if g.latest_price and g.latest_price.is_on_sale]

    out.sort(key=_SORT_KEYS[sort], reverse=(order == "desc"))
    return out


@router.post("", response_model=GameOut, status_code=201)
def add_game(payload: GameCreate, db: Session = Depends(get_db)):
    existing = db.query(Game).filter(Game.steam_appid == payload.steam_appid).first()
    if existing:
        raise HTTPException(status_code=409, detail="This game is already being tracked")

    try:
        price = fetch_game_price(payload.steam_appid)
    except SteamAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except GameNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    game = Game(
        steam_appid=payload.steam_appid,
        name=price.name,
        header_image_url=price.header_image_url,
        added_at=utcnow(),
    )
    db.add(game)
    db.flush()

    snapshot = PriceSnapshot(
        game_id=game.id,
        price_brl=price.price_brl,
        initial_price_brl=price.initial_price_brl,
        discount_percent=price.discount_percent,
        is_on_sale=price.is_on_sale,
        checked_at=utcnow(),
    )
    db.add(snapshot)
    db.commit()
    db.refresh(game)

    _backfill_history(db, game)

    return _with_latest_price(db, game)


@router.get("/{game_id}", response_model=GameOut)
def get_game(game_id: int, db: Session = Depends(get_db)):
    game = db.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return _with_latest_price(db, game)


@router.get("/{game_id}/history", response_model=GameHistoryOut)
def get_game_history(game_id: int, db: Session = Depends(get_db)):
    game = db.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return GameHistoryOut.model_validate({**game.__dict__, "history": game.price_history})


@router.delete("/{game_id}", status_code=204)
def delete_game(game_id: int, db: Session = Depends(get_db)):
    game = db.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    db.delete(game)
    db.commit()
