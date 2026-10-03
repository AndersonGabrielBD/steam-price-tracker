"""Seeds the database with a curated list of popular games -- including real
historical pricing via the ITAD backfill -- so a fresh deploy (or local demo)
doesn't start with an empty screen. Idempotent: skips games already tracked.

Reuses the exact same add-game + backfill logic the API uses (imported
directly from the router), rather than duplicating it here.

Run with (from backend/, venv active): python -m scripts.seed
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import structlog  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.logging_config import configure_logging  # noqa: E402
from app.models import Game, PriceSnapshot, utcnow  # noqa: E402
from app.routers.games import _backfill_history  # noqa: E402
from app.steam_client import GameNotFoundError, SteamAPIError, fetch_game_price  # noqa: E402

configure_logging()
logger = structlog.get_logger(__name__)

POPULAR_APPIDS = [
    730,  # Counter-Strike 2
    3240220,  # Grand Theft Auto V (Enhanced)
    1245620,  # Elden Ring
    367520,  # Hollow Knight
    413150,  # Stardew Valley
    1145360,  # Hades
    1091500,  # Cyberpunk 2077
    1174180,  # Red Dead Redemption 2
    1086940,  # Baldur's Gate 3
    620,  # Portal 2
    105600,  # Terraria
    504230,  # Celeste
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        for appid in POPULAR_APPIDS:
            existing = db.query(Game).filter(Game.steam_appid == appid).first()
            if existing:
                logger.info("seed_skip_already_tracked", appid=appid, name=existing.name)
                continue

            try:
                price = fetch_game_price(appid)
            except (SteamAPIError, GameNotFoundError) as exc:
                logger.warning("seed_skip_fetch_failed", appid=appid, error=str(exc))
                continue

            game = Game(
                steam_appid=appid,
                name=price.name,
                header_image_url=price.header_image_url,
                added_at=utcnow(),
            )
            db.add(game)
            db.flush()

            db.add(
                PriceSnapshot(
                    game_id=game.id,
                    price_brl=price.price_brl,
                    initial_price_brl=price.initial_price_brl,
                    discount_percent=price.discount_percent,
                    is_on_sale=price.is_on_sale,
                    checked_at=utcnow(),
                )
            )
            db.commit()
            db.refresh(game)

            _backfill_history(db, game)
            logger.info("seed_added", appid=appid, name=game.name)
            time.sleep(0.5)


if __name__ == "__main__":
    seed()
