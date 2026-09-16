
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class ReviewORM(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False, min_value=1, max_value=10)
    comment: Mapped[str] = mapped_column(Text, nullable=False, min_length=20, max_length=1000)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
