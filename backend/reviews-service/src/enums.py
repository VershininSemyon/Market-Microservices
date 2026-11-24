
import enum


class SortOrderEnum(str, enum.Enum):
    ASC = "asc"
    DESC = "desc"


class ReviewSortFieldEnum(str, enum.Enum):
    CREATED_AT = "created_at"
    RATING = "rating"
