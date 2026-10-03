import app.routers.games as games_module
from app.steam_client import SteamPrice


def _price(name: str, price_brl: float, discount_percent: int = 0) -> SteamPrice:
    return SteamPrice(
        name=name,
        price_brl=price_brl,
        initial_price_brl=price_brl,
        discount_percent=discount_percent,
        is_on_sale=discount_percent > 0,
        is_free=False,
        header_image_url=f"https://example.com/{name}.jpg",
    )


def _patch_price(monkeypatch, price: SteamPrice):
    monkeypatch.setattr(games_module, "fetch_game_price", lambda appid: price)


def test_add_game_persists_header_image(client, monkeypatch):
    _patch_price(monkeypatch, _price("Celeste", 30.0))

    response = client.post("/games", json={"steam_appid": 504230})

    assert response.json()["header_image_url"] == "https://example.com/Celeste.jpg"


def test_sort_by_price_ascending(client, monkeypatch):
    _patch_price(monkeypatch, _price("Expensive", 100.0))
    client.post("/games", json={"steam_appid": 1})
    _patch_price(monkeypatch, _price("Cheap", 10.0))
    client.post("/games", json={"steam_appid": 2})

    response = client.get("/games", params={"sort": "price", "order": "asc"})

    names = [g["name"] for g in response.json()]
    assert names == ["Cheap", "Expensive"]


def test_filter_on_sale_only(client, monkeypatch):
    _patch_price(monkeypatch, _price("Full Price", 50.0, discount_percent=0))
    client.post("/games", json={"steam_appid": 1})
    _patch_price(monkeypatch, _price("On Sale", 25.0, discount_percent=50))
    client.post("/games", json={"steam_appid": 2})

    response = client.get("/games", params={"on_sale_only": "true"})

    names = [g["name"] for g in response.json()]
    assert names == ["On Sale"]


def test_is_all_time_low_true_only_after_price_drops_below_previous_low(
    client, monkeypatch, db_session
):
    _patch_price(monkeypatch, _price("Game", 50.0))
    created = client.post("/games", json={"steam_appid": 1}).json()
    assert created["is_all_time_low"] is False  # single data point, not meaningful yet

    from app.models import Game, PriceSnapshot, utcnow

    game = db_session.get(Game, created["id"])
    db_session.add(PriceSnapshot(game_id=game.id, price_brl=40.0, discount_percent=20, checked_at=utcnow()))
    db_session.commit()

    response = client.get(f"/games/{created['id']}")
    assert response.json()["is_all_time_low"] is True

    db_session.add(PriceSnapshot(game_id=game.id, price_brl=45.0, discount_percent=10, checked_at=utcnow()))
    db_session.commit()

    response = client.get(f"/games/{created['id']}")
    assert response.json()["is_all_time_low"] is False
