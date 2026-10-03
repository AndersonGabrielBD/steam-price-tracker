import app.routers.games as games_module
from app.models import PriceSnapshot
from app.steam_client import SteamPrice


def _patch_price(monkeypatch, price: SteamPrice):
    monkeypatch.setattr(games_module, "fetch_game_price", lambda appid: price)


def _full_price(name: str, price_brl: float) -> SteamPrice:
    return SteamPrice(
        name=name,
        price_brl=price_brl,
        initial_price_brl=price_brl,
        discount_percent=0,
        is_on_sale=False,
        is_free=False,
    )


def test_add_game_backfills_history_when_itad_configured(client, monkeypatch, db_session):
    monkeypatch.setattr(games_module.settings, "itad_api_key", "fake-key")
    monkeypatch.setattr(games_module, "lookup_game_id", lambda appid: "itad-fake-id")
    monkeypatch.setattr(
        games_module,
        "fetch_steam_br_history",
        lambda itad_id: [
            {
                "price_brl": 23.49,
                "initial_price_brl": 46.99,
                "discount_percent": 50,
                "is_on_sale": True,
                "checked_at": "2026-06-25T19:32:03+02:00",
            },
            {
                "price_brl": 46.99,
                "initial_price_brl": 46.99,
                "discount_percent": 0,
                "is_on_sale": False,
                "checked_at": "2026-07-09T19:23:40+02:00",
            },
        ],
    )
    _patch_price(monkeypatch, _full_price("Hollow Knight", 46.99))

    created = client.post("/games", json={"steam_appid": 367520}).json()

    history = db_session.query(PriceSnapshot).filter(PriceSnapshot.game_id == created["id"]).all()
    backfilled = [h for h in history if h.source == "itad_backfill"]
    assert len(backfilled) == 2
    assert all(h.price_currency == "BRL" for h in backfilled)
    live = [h for h in history if h.source == "steam_live"]
    assert len(live) == 1


def test_add_game_skips_backfill_when_itad_not_configured(client, monkeypatch, db_session):
    # The autouse `_no_itad_backfill` fixture already clears the key, but
    # assert the behavior explicitly here rather than relying on it silently.
    monkeypatch.setattr(games_module.settings, "itad_api_key", "")
    _patch_price(monkeypatch, _full_price("Terraria", 16.0))

    created = client.post("/games", json={"steam_appid": 105600}).json()

    history = db_session.query(PriceSnapshot).filter(PriceSnapshot.game_id == created["id"]).all()
    assert len(history) == 1
    assert history[0].source == "steam_live"


def test_add_game_skips_backfill_when_itad_lookup_finds_nothing(client, monkeypatch, db_session):
    monkeypatch.setattr(games_module.settings, "itad_api_key", "fake-key")
    monkeypatch.setattr(games_module, "lookup_game_id", lambda appid: None)
    _patch_price(monkeypatch, _full_price("Obscure Game", 9.99))

    created = client.post("/games", json={"steam_appid": 999999}).json()

    history = db_session.query(PriceSnapshot).filter(PriceSnapshot.game_id == created["id"]).all()
    assert len(history) == 1
