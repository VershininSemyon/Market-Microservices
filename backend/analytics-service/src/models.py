
import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, Enum, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.enums import EntityTypeEnum, EventTypeEnum


class DayAnalyticsORM(Base):
    __tablename__ = "day_analytics"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(Enum(EntityTypeEnum), nullable=False)
    event_type: Mapped[str] = mapped_column(Enum(EventTypeEnum), nullable=False)
    occurred_at: Mapped[date] = mapped_column(Date, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("entity_type", "event_type", "occurred_at", name="unique_entity_event_occurred"),
        CheckConstraint("count > 0", name="check_count_positive")
    )
