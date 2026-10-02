import httpx
import pytest

from app.steam_client import GameNotFoundError, SteamAPIError, fetch_game_price, search_games


def _mock_response(json_data, status_code=200):
    request = httpx.Request("GET", "https://store.steampowered.com/api/appdetails")
    return httpx.Response(status_code, json=json_data, request=request)


def test_fetch_game_price_parses_discounted_price(monkeypatch):
    payload = {
        "730": {
            "success": True,
            "data": {
                "name": "Counter-Strike 2",
                "is_free": False,
                "price_overview": {
                    "currency": "BRL",
                    "initial": 5000,
                    "final": 2500,
                    "discount_percent": 50,
                },
            },
        }
    }
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _mock_response(payload))

    price = fetch_game_price(730)

    assert price.name == "Counter-Strike 2"
    assert price.price_brl == 25.0
    assert price.initial_price_brl == 50.0
    assert price.discount_percent == 50
    assert price.is_on_sale is True
    assert price.is_free is False


def test_fetch_game_price_handles_free_game(monkeypatch):
    payload = {"730": {"success": True, "data": {"name": "Team Fortress 2", "is_free": True}}}
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _mock_response(payload))

    price = fetch_game_price(730)

    assert price.is_free is True
    assert price.price_brl == 0.0


def test_fetch_game_price_raises_when_appid_unknown(monkeypatch):
    payload = {"999999999": {"success": False}}
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _mock_response(payload))

    with pytest.raises(GameNotFoundError):
        fetch_game_price(999999999)


def test_fetch_game_price_raises_without_regional_price(monkeypatch):
    payload = {"730": {"success": True, "data": {"name": "Some Game", "is_free": False}}}
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _mock_response(payload))

    with pytest.raises(GameNotFoundError):
        fetch_game_price(730)


def test_fetch_game_price_wraps_network_errors(monkeypatch):
    def _raise(*args, **kwargs):
        raise httpx.ConnectTimeout("timed out")

    monkeypatch.setattr(httpx, "get", _raise)

    with pytest.raises(SteamAPIError):
        fetch_game_price(730)


def test_search_games_returns_empty_list_on_failure(monkeypatch):
    def _raise(*args, **kwargs):
        raise httpx.ConnectTimeout("timed out")

    monkeypatch.setattr(httpx, "get", _raise)

    assert search_games("half life") == []
