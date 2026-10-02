import pytest
from celery.exceptions import Retry

import app.tasks as tasks_module
from app.models import Game, PriceSnapshot, utcnow
from app.steam_client import SteamAPIError, SteamPrice
from tests.conftest import TestingSessionLocal


def _create_game(db_session, appid=730, name="Counter-Strike 2") -> Game:
    game = Game(steam_appid=appid, name=name, added_at=utcnow())
    db_session.add(game)
    db_session.commit()
    db_session.refresh(game)
    return game


def _price(name, price_brl, initial_price_brl, discount_percent, is_on_sale) -> SteamPrice:
    return SteamPrice(
        name=name,
        price_brl=price_brl,
        initial_price_brl=initial_price_brl,
        discount_percent=discount_percent,
        is_on_sale=is_on_sale,
        is_free=False,
    )


def test_price_change_creates_new_snapshot_and_publishes(monkeypatch, db_session):
    game = _create_game(db_session)
    db_session.add(
        PriceSnapshot(
            game_id=game.id, price_brl=100.0, discount_percent=0, is_on_sale=False, checked_at=utcnow()
        )
    )
    db_session.commit()

    monkeypatch.setattr(tasks_module, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(
        tasks_module,
        "fetch_game_price",
        lambda appid: _price("Counter-Strike 2", 50.0, 100.0, 50, True),
    )
    published = []
    monkeypatch.setattr(tasks_module, "publish_price_update", lambda event: published.append(event))

    result = tasks_module.check_single_game_price(game.id)

    assert result["price_brl"] == 50.0
    assert len(published) == 1

    with TestingSessionLocal() as db:
        snapshots = db.query(PriceSnapshot).filter(PriceSnapshot.game_id == game.id).all()
        assert len(snapshots) == 2  # original + the new one


def test_unchanged_price_is_idempotent_and_does_not_duplicate(monkeypatch, db_session):
    game = _create_game(db_session)
    db_session.add(
        PriceSnapshot(
            game_id=game.id, price_brl=25.0, discount_percent=0, is_on_sale=False, checked_at=utcnow()
        )
    )
    db_session.commit()

    monkeypatch.setattr(tasks_module, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(
        tasks_module,
        "fetch_game_price",
        lambda appid: _price("Counter-Strike 2", 25.0, 25.0, 0, False),
    )
    published = []
    monkeypatch.setattr(tasks_module, "publish_price_update", lambda event: published.append(event))

    result = tasks_module.check_single_game_price(game.id)

    assert result is None
    assert published == []

    with TestingSessionLocal() as db:
        snapshots = db.query(PriceSnapshot).filter(PriceSnapshot.game_id == game.id).all()
        assert len(snapshots) == 1  # no duplicate written


def test_transient_steam_failure_triggers_retry(monkeypatch, db_session):
    game = _create_game(db_session)

    monkeypatch.setattr(tasks_module, "SessionLocal", TestingSessionLocal)

    def _raise(appid):
        raise SteamAPIError("Steam is down")

    monkeypatch.setattr(tasks_module, "fetch_game_price", _raise)

    # Calling a bound Celery task directly (bypassing the worker) makes
    # self.retry() re-raise the original exception rather than Retry, since
    # there's no live request context to reschedule against. Either way, the
    # important behavior is: it does NOT succeed silently or write a snapshot.
    with pytest.raises((Retry, SteamAPIError)):
        tasks_module.check_single_game_price(game.id)

    with TestingSessionLocal() as db:
        assert db.query(PriceSnapshot).filter(PriceSnapshot.game_id == game.id).count() == 0


def test_missing_game_is_a_noop(monkeypatch):
    monkeypatch.setattr(tasks_module, "SessionLocal", TestingSessionLocal)
    assert tasks_module.check_single_game_price(999999) is None
