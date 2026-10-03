"""Client for the IsThereAnyDeal (ITAD) API, used to backfill a newly tracked
game's price history with real past Steam-BR prices so the chart doesn't
start empty and wait weeks for our own Celery checks to build one up.

Empirically verified against the live API (tested CS2, Elden Ring, GTA V,
Hades, Stardew Valley, Cyberpunk 2077, Hollow Knight): ITAD's history
endpoint mixes multiple stores and currencies when unfiltered (BRL, USD,
etc. all in the same response), but filtering to shop id 61 ("Steam") with
country=br consistently returns prices in BRL. So we only ever backfill
Steam-sourced, BRL-denominated points -- no currency-conversion or
"reference price" labeling trick needed.
"""

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

ITAD_STEAM_SHOP_ID = 61


class ItadAPIError(Exception):
    """Raised on network/HTTP failures talking to ITAD."""


def _get(path: str, params: dict) -> dict | list:
    try:
        response = httpx.get(
            f"{settings.itad_base_url}{path}",
            params={**params, "key": settings.itad_api_key},
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ItadAPIError(f"Failed to reach ITAD API ({path}): {exc}") from exc
    return response.json()


def lookup_game_id(steam_appid: int) -> str | None:
    """Resolves a Steam appid to ITAD's internal game id. Returns None if ITAD
    has no record of this game (not an error -- plenty of valid Steam games,
    especially very new or very obscure ones, aren't in ITAD's catalog).
    """
    data = _get("/games/lookup/v1", {"appid": steam_appid})
    if not data.get("found"):
        return None
    return data["game"]["id"]


def fetch_steam_br_history(itad_game_id: str) -> list[dict]:
    """Returns real historical Steam-BR price points (last ~3 months, ITAD's
    own default window) as raw dicts with keys: price_brl, initial_price_brl,
    discount_percent, is_on_sale, checked_at (ISO 8601 string).
    """
    data = _get(
        "/games/history/v2",
        {"id": itad_game_id, "country": "br", "shops": ITAD_STEAM_SHOP_ID},
    )
    points = []
    for entry in data:
        deal = entry["deal"]
        if deal["price"]["currency"] != "BRL":
            # Shouldn't happen given the shop+country filter above, but better
            # to skip a surprising point than silently store a wrong number.
            logger.warning("itad_unexpected_currency", currency=deal["price"]["currency"])
            continue
        points.append(
            {
                "price_brl": deal["price"]["amount"],
                "initial_price_brl": deal["regular"]["amount"],
                "discount_percent": deal["cut"],
                "is_on_sale": deal["cut"] > 0,
                "checked_at": entry["timestamp"],
            }
        )
    return points
