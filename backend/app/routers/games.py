from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Game, PriceSnapshot, utcnow
from app.schemas import GameCreate, GameHistoryOut, GameOut
from app.steam_client import GameNotFoundError, SteamAPIError, fetch_game_price, search_games

router = APIRouter(prefix="/games", tags=["games"])


def _with_latest_price(db: Session, game: Game) -> GameOut:
    latest = (
        db.query(PriceSnapshot)
        .filter(PriceSnapshot.game_id == game.id)
        .order_by(PriceSnapshot.checked_at.desc())
        .first()
    )
    return GameOut.model_validate({**game.__dict__, "latest_price": latest})


@router.get("/search")
def search(q: str = Query(min_length=2)):
    """Best-effort search by name, to help pick a Steam appid in the UI."""
    return search_games(q)


@router.get("", response_model=list[GameOut])
def list_games(db: Session = Depends(get_db)):
    games = db.query(Game).order_by(Game.added_at.desc()).all()
    return [_with_latest_price(db, game) for game in games]


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

    game = Game(steam_appid=payload.steam_appid, name=price.name, added_at=utcnow())
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
