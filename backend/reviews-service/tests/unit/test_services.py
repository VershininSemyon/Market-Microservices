
import json
import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import src.services as services_module
from src.config import settings
from src.enums import ReviewSortFieldEnum, SortOrderEnum
from src.exceptions import (
    ProductNotFoundError,
    ReviewAlreadyExistsError,
    ReviewNotFoundError,
    ReviewOwnershipError,
)
from src.schemas import (
    ReviewCreateSchema,
    ReviewListResponseSchema,
    ReviewQueryParams,
    ReviewReadSchema,
    ReviewUpdateSchema,
)
from src.services import ReviewService


class FakeUnitOfWork:
    def __init__(self, review_repo: AsyncMock):
        self.review_repo = review_repo
        self.commit = AsyncMock()
        self.rollback = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


COMMENT = "This is a very good product"


def make_review(**overrides) -> SimpleNamespace:
    data = {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "product_id": uuid.uuid4(),
        "rating": 8,
        "comment": COMMENT,
        "created_at": datetime.now(timezone.utc),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


@pytest.fixture
def review_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def uow(review_repo: AsyncMock) -> FakeUnitOfWork:
    return FakeUnitOfWork(review_repo)


@pytest.fixture
def service(uow: FakeUnitOfWork) -> ReviewService:
    return ReviewService(uow)


@pytest.fixture(autouse=True)
def external(monkeypatch) -> SimpleNamespace:
    mocks = SimpleNamespace(
        check_product_exists=AsyncMock(),
        redis_cache=SimpleNamespace(
            set_value=AsyncMock(),
            get_value=AsyncMock(),
            del_key=AsyncMock(),
        ),
        rabbitmq_producer=SimpleNamespace(publish_message=AsyncMock()),
    )

    monkeypatch.setattr(services_module, "check_product_exists", mocks.check_product_exists)
    monkeypatch.setattr(services_module, "redis_cache", mocks.redis_cache)
    monkeypatch.setattr(services_module, "rabbitmq_producer", mocks.rabbitmq_producer)

    return mocks


async def test_invalidate_review_list_cache(service, external) -> None:
    product_id = uuid.uuid4()

    await service.invalidate_review_list_cache(product_id)

    external.redis_cache.del_key.assert_awaited_once_with(f"reviews:{product_id}:list")


async def test_create_review_success(service, uow, review_repo, external) -> None:
    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    review = make_review(user_id=user_id, product_id=product_id)
    review_repo.get_review_by_user_and_product.return_value = None
    review_repo.create_review.return_value = review
    data = ReviewCreateSchema(product_id=product_id, rating=8, comment=COMMENT)

    result = await service.create_review(data, user_id, "alice@example.com")

    assert isinstance(result, ReviewReadSchema)
    assert result.id == review.id
    external.check_product_exists.assert_awaited_once_with(product_id)
    review_repo.get_review_by_user_and_product.assert_awaited_once_with(
        user_id=user_id,
        product_id=product_id,
    )
    review_repo.create_review.assert_awaited_once_with(
        {**data.model_dump(), "user_id": user_id}
    )
    uow.commit.assert_awaited_once()
    external.redis_cache.del_key.assert_awaited_once_with(f"reviews:{product_id}:list")
    external.rabbitmq_producer.publish_message.assert_awaited_once_with(
        routing_key=settings.REVIEW_CREATED_ROUTING_KEY,
        message_body={
            "product_id": str(product_id),
            "user_email": "alice@example.com",
            "event_date": date.today().isoformat(),
        },
    )


async def test_create_review_raises_when_product_not_found(service, uow, review_repo, external) -> None:
    external.check_product_exists.side_effect = ProductNotFoundError()
    data = ReviewCreateSchema(product_id=uuid.uuid4(), rating=8, comment=COMMENT)

    with pytest.raises(ProductNotFoundError):
        await service.create_review(data, uuid.uuid4(), "alice@example.com")

    review_repo.create_review.assert_not_awaited()
    uow.commit.assert_not_awaited()


async def test_create_review_raises_when_already_exists(service, uow, review_repo, external) -> None:
    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    review_repo.get_review_by_user_and_product.return_value = make_review(
        user_id=user_id,
        product_id=product_id,
    )
    data = ReviewCreateSchema(product_id=product_id, rating=8, comment=COMMENT)

    with pytest.raises(ReviewAlreadyExistsError):
        await service.create_review(data, user_id, "alice@example.com")

    review_repo.create_review.assert_not_awaited()
    uow.commit.assert_not_awaited()
    external.rabbitmq_producer.publish_message.assert_not_awaited()


async def test_get_product_reviews_returns_cached_data(service, review_repo, external) -> None:
    product_id = uuid.uuid4()
    review = make_review(product_id=product_id)
    cached = ReviewListResponseSchema(
        reviews=[ReviewReadSchema.model_validate(review)],
        avg_rating=8.0,
    )
    external.redis_cache.get_value.return_value = cached.model_dump_json()

    result = await service.get_product_reviews(ReviewQueryParams(product_id=product_id))

    assert result.avg_rating == 8.0
    assert len(result.reviews) == 1
    external.check_product_exists.assert_awaited_once_with(product_id)
    review_repo.get_reviews_by_product_id.assert_not_awaited()
    external.redis_cache.set_value.assert_not_awaited()


async def test_get_product_reviews_caches_result_on_miss(service, review_repo, external) -> None:
    product_id = uuid.uuid4()
    review = make_review(product_id=product_id)
    external.redis_cache.get_value.return_value = None
    review_repo.get_reviews_by_product_id.return_value = [review]
    review_repo.get_product_avg_rating.return_value = 8.0

    result = await service.get_product_reviews(ReviewQueryParams(product_id=product_id))

    assert result.avg_rating == 8.0
    assert len(result.reviews) == 1
    review_repo.get_reviews_by_product_id.assert_awaited_once_with(
        product_id,
        order_by=None,
        order=SortOrderEnum.ASC,
        limit=10,
        offset=0,
    )
    review_repo.get_product_avg_rating.assert_awaited_once_with(product_id)
    external.redis_cache.set_value.assert_awaited_once()
    key, value, ttl = external.redis_cache.set_value.call_args.args
    assert key == f"reviews:{product_id}:list"
    assert ttl == 3600 * 24 * 7
    assert json.loads(value)["avg_rating"] == 8.0


async def test_get_product_reviews_passes_sorting_and_pagination_without_cache(
    service,
    review_repo,
    external,
) -> None:
    product_id = uuid.uuid4()
    review = make_review(product_id=product_id)
    review_repo.get_reviews_by_product_id.return_value = [review]
    review_repo.get_product_avg_rating.return_value = 8.0
    filters = ReviewQueryParams(
        product_id=product_id,
        order_by=ReviewSortFieldEnum.RATING,
        order=SortOrderEnum.DESC,
        limit=5,
        offset=2,
    )

    result = await service.get_product_reviews(filters)

    assert len(result.reviews) == 1
    review_repo.get_reviews_by_product_id.assert_awaited_once_with(
        product_id,
        order_by=ReviewSortFieldEnum.RATING,
        order=SortOrderEnum.DESC,
        limit=5,
        offset=2,
    )
    external.redis_cache.get_value.assert_not_awaited()
    external.redis_cache.set_value.assert_not_awaited()


async def test_get_product_reviews_passes_date_sorting(service, review_repo, external) -> None:
    product_id = uuid.uuid4()
    review_repo.get_reviews_by_product_id.return_value = [make_review(product_id=product_id)]
    review_repo.get_product_avg_rating.return_value = 8.0
    filters = ReviewQueryParams(
        product_id=product_id,
        order_by=ReviewSortFieldEnum.CREATED_AT,
        order=SortOrderEnum.ASC,
    )

    await service.get_product_reviews(filters)

    review_repo.get_reviews_by_product_id.assert_awaited_once_with(
        product_id,
        order_by=ReviewSortFieldEnum.CREATED_AT,
        order=SortOrderEnum.ASC,
        limit=10,
        offset=0,
    )


async def test_get_product_reviews_raises_when_product_not_found(service, external) -> None:
    external.check_product_exists.side_effect = ProductNotFoundError()

    with pytest.raises(ProductNotFoundError):
        await service.get_product_reviews(ReviewQueryParams(product_id=uuid.uuid4()))

    external.redis_cache.get_value.assert_not_awaited()


async def test_get_review_by_id_success(service, review_repo) -> None:
    review = make_review()
    review_repo.get_review_by_id.return_value = review

    result = await service.get_review_by_id(review.id)

    assert result.id == review.id
    review_repo.get_review_by_id.assert_awaited_once_with(review.id)


async def test_get_review_by_id_raises_when_not_found(service, review_repo) -> None:
    review_repo.get_review_by_id.return_value = None

    with pytest.raises(ReviewNotFoundError):
        await service.get_review_by_id(uuid.uuid4())


async def test_delete_review_success(service, uow, review_repo, external) -> None:
    user_id = uuid.uuid4()
    review = make_review(user_id=user_id)
    review_repo.get_review_by_id.return_value = review

    await service.delete_review(review.id, user_id, "alice@example.com")

    review_repo.delete_review.assert_awaited_once_with(review.id)
    uow.commit.assert_awaited_once()
    external.redis_cache.del_key.assert_awaited_once_with(f"reviews:{review.product_id}:list")
    external.rabbitmq_producer.publish_message.assert_awaited_once_with(
        routing_key=settings.REVIEW_DELETED_ROUTING_KEY,
        message_body={
            "product_id": str(review.product_id),
            "user_email": "alice@example.com",
            "event_date": date.today().isoformat(),
        },
    )


async def test_delete_review_raises_when_not_found(service, uow, review_repo, external) -> None:
    review_repo.get_review_by_id.return_value = None

    with pytest.raises(ReviewNotFoundError):
        await service.delete_review(uuid.uuid4(), uuid.uuid4(), "alice@example.com")

    review_repo.delete_review.assert_not_awaited()
    uow.commit.assert_not_awaited()
    external.rabbitmq_producer.publish_message.assert_not_awaited()


async def test_delete_review_raises_when_not_owner(service, uow, review_repo, external) -> None:
    review_repo.get_review_by_id.return_value = make_review()

    with pytest.raises(ReviewOwnershipError):
        await service.delete_review(uuid.uuid4(), uuid.uuid4(), "alice@example.com")

    review_repo.delete_review.assert_not_awaited()
    uow.commit.assert_not_awaited()
    external.rabbitmq_producer.publish_message.assert_not_awaited()


async def test_update_review_success(service, uow, review_repo, external) -> None:
    user_id = uuid.uuid4()
    review = make_review(user_id=user_id)
    updated_review = make_review(
        id=review.id,
        user_id=user_id,
        product_id=review.product_id,
        rating=10,
        comment="Updated comment with enough length",
    )
    review_repo.get_review_by_id.return_value = review
    review_repo.update_review.return_value = updated_review
    data = ReviewUpdateSchema(rating=10, comment="Updated comment with enough length")

    result = await service.update_review(review.id, data, user_id)

    assert result.rating == 10
    review_repo.update_review.assert_awaited_once_with(review.id, data.model_dump())
    uow.commit.assert_awaited_once()
    external.redis_cache.del_key.assert_awaited_once_with(f"reviews:{review.product_id}:list")


async def test_update_review_raises_when_not_found(service, review_repo, external) -> None:
    review_repo.get_review_by_id.return_value = None
    data = ReviewUpdateSchema(rating=10, comment="Updated comment with enough length")

    with pytest.raises(ReviewNotFoundError):
        await service.update_review(uuid.uuid4(), data, uuid.uuid4())

    review_repo.update_review.assert_not_awaited()
    external.redis_cache.del_key.assert_not_awaited()


async def test_update_review_raises_when_not_owner(service, review_repo, external) -> None:
    review_repo.get_review_by_id.return_value = make_review()
    data = ReviewUpdateSchema(rating=10, comment="Updated comment with enough length")

    with pytest.raises(ReviewOwnershipError):
        await service.update_review(uuid.uuid4(), data, uuid.uuid4())

    review_repo.update_review.assert_not_awaited()
    external.redis_cache.del_key.assert_not_awaited()
