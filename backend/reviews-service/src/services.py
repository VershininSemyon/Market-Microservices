
from src.config import settings
from src.exceptions import ReviewAlreadyExistsError, ReviewNotFoundError, ReviewOwnershipError
from src.producer import rabbitmq_producer
from src.products_api_client import check_product_exists
from src.schemas import ReviewCreateSchema, ReviewListResponseSchema, ReviewReadSchema, ReviewUpdateSchema
from src.unitofwork import UnitOfWork


class ReviewService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_review(self, data: ReviewCreateSchema, user_id: str, user_email: str) -> ReviewReadSchema:
        async with self.uow:
            await check_product_exists(data.product_id)

            review_exists = await self.uow.review_repo.get_review_by_user_and_product(
                user_id=user_id,
                product_id=data.product_id
            )

            if review_exists:
                raise ReviewAlreadyExistsError()

            data = {
                **data.model_dump(),
                "user_id": user_id
            }

            review = await self.uow.review_repo.create_review(data)
            await self.uow.commit()

        await rabbitmq_producer.publish_message(
            routing_key=settings.REVIEW_CREATED_ROUTING_KEY,
            message_body={
                "product_id": str(review.product_id),
                "user_email": user_email
            }
        )
        return ReviewReadSchema.model_validate(review)

    async def get_product_reviews(self, product_id: str) -> ReviewListResponseSchema:
        await check_product_exists(product_id)

        async with self.uow:
            reviews = await self.uow.review_repo.get_reviews_by_product_id(product_id)
            product_avg_rating = await self.uow.review_repo.get_product_avg_rating(product_id)

        reviews = [ReviewReadSchema.model_validate(review) for review in reviews]
        return ReviewListResponseSchema(reviews=reviews, avg_rating=product_avg_rating)

    async def get_review_by_id(self, review_id: str) -> ReviewReadSchema:
        async with self.uow:
            review = await self.uow.review_repo.get_review_by_id(review_id)

        if not review:
            raise ReviewNotFoundError()

        return ReviewReadSchema.model_validate(review)

    async def delete_review(self, review_id: str, user_id: str, user_email: str) -> None:
        async with self.uow:
            review = await self.uow.review_repo.get_review_by_id(review_id)

            if not review:
                raise ReviewNotFoundError()

            if review.user_id != user_id:
                raise ReviewOwnershipError()

            await self.uow.review_repo.delete_review(review_id)
            await self.uow.commit()

        await rabbitmq_producer.publish_message(
            routing_key=settings.REVIEW_DELETED_ROUTING_KEY,
            message_body={
                "product_id": str(review.product_id),
                "user_email": user_email
            }
        )

    async def update_review(self, review_id: str, data: ReviewUpdateSchema, user_id: str) -> ReviewReadSchema:
        async with self.uow:
            review = await self.uow.review_repo.get_review_by_id(review_id)

            if not review:
                raise ReviewNotFoundError()

            if review.user_id != user_id:
                raise ReviewOwnershipError()

            updated_review = await self.uow.review_repo.update_review(review_id, data.model_dump())
            await self.uow.commit()

        return ReviewReadSchema.model_validate(updated_review)
