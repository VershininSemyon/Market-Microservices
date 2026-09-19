
import enum


class EntityTypeEnum(str, enum.Enum):
    USER = "user"
    PRODUCT = "product"
    REVIEW = "review"
    ORDER = "order"


class EventTypeEnum(str, enum.Enum):
    CREATED = "created"
    DELETED = "deleted"


class PeriodEnum(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    ALL = "all"
