
from datetime import date
from typing import Annotated

from pydantic import BaseModel, Field

from src.enums import EntityTypeEnum, EventTypeEnum


class AnalyticsStatsSchema(BaseModel):
    distribution: dict[EntityTypeEnum, dict[EventTypeEnum, int]]
    total_created: int
    total_deleted: int


class EventDateMessageSchema(BaseModel):
    event_date: Annotated[date, Field(default_factory=date.today)]
