
import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

ReviewRating = Annotated[int, Field(ge=1, le=10)]
ReviewComment = Annotated[str, Field(min_length=20, max_length=1000)]


class ReviewReadSchema(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    product_id: uuid.UUID
    rating: ReviewRating
    comment: ReviewComment
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewListResponseSchema(BaseModel):
    reviews: list[ReviewReadSchema]
    avg_rating: float


class ReviewCreateSchema(BaseModel):
    product_id: uuid.UUID
    rating: ReviewRating
    comment: ReviewComment


class ReviewUpdateSchema(BaseModel):
    rating: ReviewRating
    comment: ReviewComment
