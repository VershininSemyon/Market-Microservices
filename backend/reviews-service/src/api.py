
from uuid import UUID

from fastapi import APIRouter, status

from src.dependencies import CurrentUserDep, ReviewServiceDep
from src.schemas import ReviewCreateSchema, ReviewListResponseSchema, ReviewReadSchema, ReviewUpdateSchema

review_router = APIRouter(prefix="/reviews", tags=["Reviews"])


@review_router.post(
    "/",
    response_model=ReviewReadSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    data: ReviewCreateSchema,
    review_service: ReviewServiceDep,
    user: CurrentUserDep,
) -> ReviewReadSchema:
    return await review_service.create_review(data, user.id, user.email)


@review_router.get(
    "/",
    response_model=ReviewListResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_product_reviews(
    product_id: UUID,
    review_service: ReviewServiceDep,
) -> ReviewListResponseSchema:
    return await review_service.get_product_reviews(product_id)


@review_router.get(
    "/{review_id}",
    response_model=ReviewReadSchema,
    status_code=status.HTTP_200_OK,
)
async def get_review_by_id(
    review_id: UUID,
    review_service: ReviewServiceDep,
) -> ReviewReadSchema:
    return await review_service.get_review_by_id(review_id)


@review_router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_review(
    review_id: UUID,
    review_service: ReviewServiceDep,
    user: CurrentUserDep,
) -> None:
    await review_service.delete_review(review_id, user.id, user.email)


@review_router.put(
    "/{review_id}",
    response_model=ReviewReadSchema,
    status_code=status.HTTP_200_OK,
)
async def update_review(
    review_id: UUID,
    data: ReviewUpdateSchema,
    review_service: ReviewServiceDep,
    user: CurrentUserDep,
) -> ReviewReadSchema:
    return await review_service.update_review(review_id, data, user.id)
