
from datetime import date

import pytest
from pydantic import ValidationError

from src.enums import EntityTypeEnum, EventTypeEnum
from src.schemas import AnalyticsStatsSchema, EventDateMessageSchema


def test_event_date_message_schema_parses_date() -> None:
    schema = EventDateMessageSchema.model_validate({"event_date": "2026-01-15"})

    assert schema.event_date == date(2026, 1, 15)


def test_event_date_message_schema_defaults_to_today() -> None:
    schema = EventDateMessageSchema.model_validate({})

    assert schema.event_date == date.today()


def test_event_date_message_schema_rejects_invalid_date() -> None:
    with pytest.raises(ValidationError):
        EventDateMessageSchema.model_validate({"event_date": "not-a-date"})


def test_analytics_stats_schema_parses_distribution() -> None:
    schema = AnalyticsStatsSchema(
        distribution={
            EntityTypeEnum.USER: {EventTypeEnum.CREATED: 3},
            EntityTypeEnum.PRODUCT: {
                EventTypeEnum.CREATED: 1,
                EventTypeEnum.DELETED: 2,
            },
        },
        total_created=4,
        total_deleted=2,
    )

    assert schema.distribution[EntityTypeEnum.USER][EventTypeEnum.CREATED] == 3
    assert schema.total_created == 4
    assert schema.total_deleted == 2


def test_analytics_stats_schema_requires_all_totals() -> None:
    with pytest.raises(ValidationError):
        AnalyticsStatsSchema(distribution={}, total_created=1)
