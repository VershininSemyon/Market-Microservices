
import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, Float, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class ExchangeTypeEnum(enum.Enum):
    DIRECT: str = "direct"
    FANOUT: str = "fanout"
    TOPIC: str = "topic"


class OrderORM(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    products: Mapped[dict] = mapped_column(JSONB, nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("total_price > 0", name="check_total_price_positive"),
        CheckConstraint("total_amount >= 0", name="check_total_amount_non_negative")
    )


class OutboxEventORM(Base):
    __tablename__ = "outbox_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    exchange_name: Mapped[str] = mapped_column(Text, nullable=False)
    exchange_type: Mapped[str] = mapped_column(Enum(ExchangeTypeEnum), nullable=False)
    routing_key: Mapped[str] = mapped_column(Text, nullable=False)
    event_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
