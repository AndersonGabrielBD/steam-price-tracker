from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GameCreate(BaseModel):
    steam_appid: int


class PriceSnapshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    price_brl: float
    initial_price_brl: float | None
    discount_percent: int
    is_on_sale: bool
    source: str
    price_currency: str
    checked_at: datetime


class GameOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    steam_appid: int
    name: str
    header_image_url: str | None = None
    added_at: datetime
    latest_price: PriceSnapshotOut | None = None
    is_all_time_low: bool = False


class GameHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    steam_appid: int
    name: str
    history: list[PriceSnapshotOut]


class PriceUpdateEvent(BaseModel):
    """Payload broadcast over the WebSocket when a tracked game's price changes."""

    game_id: int
    steam_appid: int
    name: str
    price_brl: float
    discount_percent: int
    is_on_sale: bool
    checked_at: datetime
