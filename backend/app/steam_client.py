"""Thin client around the (unofficial but widely used) Steam Store API.

We request prices with cc=br so Steam returns the actual regional price it
charges in Brazil (BRL), instead of converting a USD price ourselves.
"""

from dataclasses import dataclass

import httpx

from app.config import settings


class SteamAPIError(Exception):
    """Raised on network/HTTP failures. Celery tasks retry on this."""


class GameNotFoundError(Exception):
    """Raised when Steam has no app with the given id, or no BR pricing."""


@dataclass
class SteamPrice:
    name: str
    price_brl: float
    initial_price_brl: float
    discount_percent: int
    is_on_sale: bool
    is_free: bool


def fetch_game_price(appid: int, timeout: float = 10.0) -> SteamPrice:
    url = f"{settings.steam_api_base_url}/appdetails"
    params = {
        "appids": appid,
        "cc": settings.steam_region_cc,
        "l": settings.steam_region_lang,
    }
    try:
        response = httpx.get(url, params=params, timeout=timeout)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise SteamAPIError(f"Failed to reach Steam API for appid={appid}: {exc}") from exc

    payload = response.json()
    entry = payload.get(str(appid))
    if not entry or not entry.get("success"):
        raise GameNotFoundError(f"Steam has no data for appid={appid}")

    data = entry["data"]

    if data.get("is_free"):
        return SteamPrice(
            name=data["name"],
            price_brl=0.0,
            initial_price_brl=0.0,
            discount_percent=0,
            is_on_sale=False,
            is_free=True,
        )

    price_overview = data.get("price_overview")
    if not price_overview:
        raise GameNotFoundError(
            f"appid={appid} has no price_overview (likely unavailable in region 'br')"
        )

    return SteamPrice(
        name=data["name"],
        price_brl=price_overview["final"] / 100,
        initial_price_brl=price_overview["initial"] / 100,
        discount_percent=price_overview["discount_percent"],
        is_on_sale=price_overview["discount_percent"] > 0,
        is_free=False,
    )


def search_games(term: str, timeout: float = 10.0) -> list[dict]:
    """Best-effort search by name, used by the "add game" UI.

    Uses the unofficial storesearch endpoint. Falls back to an empty list on
    any failure so a flaky search never breaks the rest of the app -- the
    user can still add a game directly by its Steam appid.
    """
    url = "https://store.steampowered.com/api/storesearch/"
    params = {"term": term, "cc": settings.steam_region_cc, "l": settings.steam_region_lang}
    try:
        response = httpx.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        items = response.json().get("items", [])
    except (httpx.HTTPError, ValueError):
        return []

    return [{"appid": item["id"], "name": item["name"]} for item in items]
