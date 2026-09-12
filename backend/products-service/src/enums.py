

import enum


class SortOrderEnum(str, enum.Enum):
    ASC = "asc"
    DESC = "desc"


class ProductSortFieldEnum(str, enum.Enum):
    PRICE = "price"
    NAME = "name"
