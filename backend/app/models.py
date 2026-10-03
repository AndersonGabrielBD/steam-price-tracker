from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    steam_appid: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    header_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    price_history: Mapped[list["PriceSnapshot"]] = relationship(
        back_populates="game", cascade="all, delete-orphan", order_by="PriceSnapshot.checked_at"
    )


class PriceSnapshot(Base):
    __tablename__ = "price_history"
    __table_args__ = (
        Index("ix_price_history_game_checked_at", "game_id", "checked_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    price_brl: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    initial_price_brl: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    discount_percent: Mapped[int] = mapped_column(Integer, default=0)
    is_on_sale: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(20), default="steam_live", nullable=False)
    price_currency: Mapped[str] = mapped_column(String(3), default="BRL", nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    game: Mapped["Game"] = relationship(back_populates="price_history")


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    target_price_brl: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    game: Mapped["Game"] = relationship()
