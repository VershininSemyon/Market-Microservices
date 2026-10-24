
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, Integer, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


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
