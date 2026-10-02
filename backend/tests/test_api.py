import app.routers.games as games_module
from app.steam_client import GameNotFoundError, SteamPrice


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


def test_add_game_creates_game_and_first_snapshot(client, monkeypatch):
    _patch_price(
        monkeypatch,
        SteamPrice(
            name="Hollow Knight",
            price_brl=19.99,
            initial_price_brl=39.99,
            discount_percent=50,
            is_on_sale=True,
            is_free=False,
        ),
    )

    response = client.post("/games", json={"steam_appid": 367520})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Hollow Knight"
    assert body["steam_appid"] == 367520
    assert body["latest_price"]["price_brl"] == 19.99
    assert body["latest_price"]["is_on_sale"] is True


def test_add_game_twice_returns_409(client, monkeypatch):
    _patch_price(monkeypatch, _full_price("Hades", 10))

    first = client.post("/games", json={"steam_appid": 1145360})
    second = client.post("/games", json={"steam_appid": 1145360})

    assert first.status_code == 201
    assert second.status_code == 409


def test_add_unknown_appid_returns_404(client, monkeypatch):
    def _raise(appid):
        raise GameNotFoundError(f"no data for {appid}")

    monkeypatch.setattr(games_module, "fetch_game_price", _raise)

    response = client.post("/games", json={"steam_appid": 1})

    assert response.status_code == 404


def test_list_games_includes_latest_price(client, monkeypatch):
    _patch_price(monkeypatch, _full_price("Stardew Valley", 22.0))
    client.post("/games", json={"steam_appid": 413150})

    response = client.get("/games")

    assert response.status_code == 200
    games = response.json()
    assert len(games) == 1
    assert games[0]["latest_price"]["price_brl"] == 22.0


def test_get_game_history_returns_all_snapshots(client, monkeypatch, db_session):
    _patch_price(monkeypatch, _full_price("Celeste", 30.0))
    created = client.post("/games", json={"steam_appid": 504230}).json()

    response = client.get(f"/games/{created['id']}/history")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Celeste"
    assert len(body["history"]) == 1
    assert body["history"][0]["price_brl"] == 30.0


def test_get_missing_game_returns_404(client):
    response = client.get("/games/999")
    assert response.status_code == 404


def test_delete_game_removes_it(client, monkeypatch):
    _patch_price(monkeypatch, _full_price("Terraria", 16.0))
    created = client.post("/games", json={"steam_appid": 105600}).json()

    delete_response = client.delete(f"/games/{created['id']}")
    get_response = client.get(f"/games/{created['id']}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404
