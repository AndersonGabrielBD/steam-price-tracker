import structlog

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import Game, PriceSnapshot, utcnow
from app.pubsub import publish_price_update
from app.steam_client import GameNotFoundError, SteamAPIError, fetch_game_price

logger = structlog.get_logger(__name__)


@celery_app.task
def check_all_game_prices() -> int:
    """Beat-scheduled task: fan out one check task per tracked game so a
    single slow/failing game can't block the others.
    """
    with SessionLocal() as db:
        game_ids = [row[0] for row in db.query(Game.id).all()]

    for game_id in game_ids:
        check_single_game_price.delay(game_id)

    return len(game_ids)


@celery_app.task(bind=True, max_retries=3)
def check_single_game_price(self, game_id: int) -> dict | None:
    with SessionLocal() as db:
        game = db.get(Game, game_id)
        if game is None:
            logger.warning("game_not_found_in_db", game_id=game_id)
            return None

        try:
            price = fetch_game_price(game.steam_appid)
        except SteamAPIError as exc:
            # Transient failure (network/HTTP) -- retry with exponential backoff.
            raise self.retry(exc=exc, countdown=30 * (2**self.request.retries))
        except GameNotFoundError as exc:
            # Permanent-ish failure for this appid -- don't retry, just log.
            logger.warning("game_not_found_on_steam", game_id=game_id, error=str(exc))
            return None

        last_snapshot = (
            db.query(PriceSnapshot)
            .filter(PriceSnapshot.game_id == game.id)
            .order_by(PriceSnapshot.checked_at.desc())
            .first()
        )

        price_unchanged = last_snapshot is not None and (
            float(last_snapshot.price_brl) == price.price_brl
            and last_snapshot.discount_percent == price.discount_percent
        )
        if price_unchanged:
            # Idempotency: don't write a new row every run if nothing changed,
            # otherwise price_history would grow unbounded with duplicates.
            return None

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
        db.refresh(snapshot)

        event = {
            "game_id": game.id,
            "steam_appid": game.steam_appid,
            "name": game.name,
            "price_brl": price.price_brl,
            "discount_percent": price.discount_percent,
            "is_on_sale": price.is_on_sale,
            "checked_at": snapshot.checked_at,
        }
        publish_price_update(event)
        return event
