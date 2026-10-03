import csv
import io

import app.routers.games as games_module
from app.steam_client import SteamPrice


def _price(name: str, price_brl: float) -> SteamPrice:
    return SteamPrice(
        name=name,
        price_brl=price_brl,
        initial_price_brl=price_brl,
        discount_percent=0,
        is_on_sale=False,
        is_free=False,
    )


def test_add_game_rate_limit_trips_after_ten_per_minute(client, monkeypatch):
    monkeypatch.setattr(games_module, "fetch_game_price", lambda appid: _price(f"Game {appid}", 10.0))

    statuses = [client.post("/games", json={"steam_appid": appid}).status_code for appid in range(1, 12)]

    assert statuses[:10] == [201] * 10
    assert statuses[10] == 429


def test_search_rate_limit_trips_after_twenty_per_minute(client, monkeypatch):
    monkeypatch.setattr(games_module, "search_games", lambda term: [])

    statuses = [client.get("/games/search", params={"q": "half life"}).status_code for _ in range(21)]

    assert statuses[:20] == [200] * 20
    assert statuses[20] == 429


def test_history_csv_contains_all_snapshots(client, monkeypatch):
    monkeypatch.setattr(games_module, "fetch_game_price", lambda appid: _price("Celeste", 30.0))
    created = client.post("/games", json={"steam_appid": 504230}).json()

    response = client.get(f"/games/{created['id']}/history.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "Celeste_price_history.csv" in response.headers["content-disposition"]

    rows = list(csv.reader(io.StringIO(response.text)))
    assert rows[0] == [
        "checked_at",
        "price_brl",
        "initial_price_brl",
        "discount_percent",
        "is_on_sale",
        "source",
    ]
    assert len(rows) == 2  # header + one live snapshot
    assert rows[1][1] == "30.00"
    assert rows[1][5] == "steam_live"


def test_history_csv_404_for_missing_game(client):
    response = client.get("/games/999/history.csv")
    assert response.status_code == 404
