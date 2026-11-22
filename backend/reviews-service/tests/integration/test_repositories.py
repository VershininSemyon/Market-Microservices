
import uuid

from src.repositories import ReviewRepository

COMMENT = "This is a very good product"


def make_data(**overrides) -> dict:
    data = {
        "user_id": uuid.uuid4(),
        "product_id": uuid.uuid4(),
        "rating": 8,
        "comment": COMMENT,
    }
    data.update(overrides)
    return data


async def test_create_review_returns_persisted_entity(db_session) -> None:
    repo = ReviewRepository(db_session)

    review = await repo.create_review(make_data())
    await db_session.commit()

    assert review is not None
    assert isinstance(review.id, uuid.UUID)
    assert review.rating == 8
    assert review.created_at is not None


async def test_get_review_by_id(db_session) -> None:
    repo = ReviewRepository(db_session)
    created = await repo.create_review(make_data())
    await db_session.commit()

    review = await repo.get_review_by_id(created.id)

    assert review is not None
    assert review.id == created.id


async def test_get_review_by_id_returns_none_for_unknown_id(db_session) -> None:
    repo = ReviewRepository(db_session)

    assert await repo.get_review_by_id(uuid.uuid4()) is None


async def test_get_reviews_by_product_id(db_session) -> None:
    repo = ReviewRepository(db_session)
    product_id = uuid.uuid4()
    await repo.create_review(make_data(product_id=product_id))
    await repo.create_review(make_data(product_id=product_id))
    await repo.create_review(make_data())
    await db_session.commit()

    reviews = await repo.get_reviews_by_product_id(product_id)

    assert len(reviews) == 2
    assert all(review.product_id == product_id for review in reviews)


async def test_get_review_by_user_and_product(db_session) -> None:
    repo = ReviewRepository(db_session)
    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    await repo.create_review(make_data(user_id=user_id, product_id=product_id))
    await db_session.commit()

    review = await repo.get_review_by_user_and_product(user_id, product_id)

    assert review is not None
    assert review.user_id == user_id
    assert review.product_id == product_id


async def test_get_review_by_user_and_product_returns_none(db_session) -> None:
    repo = ReviewRepository(db_session)

    assert await repo.get_review_by_user_and_product(uuid.uuid4(), uuid.uuid4()) is None


async def test_get_product_avg_rating(db_session) -> None:
    repo = ReviewRepository(db_session)
    product_id = uuid.uuid4()
    await repo.create_review(make_data(product_id=product_id, rating=8))
    await repo.create_review(make_data(product_id=product_id, rating=10))
    await repo.create_review(make_data(rating=1))
    await db_session.commit()

    avg_rating = await repo.get_product_avg_rating(product_id)

    assert avg_rating == 9.0


async def test_get_product_avg_rating_returns_zero_without_reviews(db_session) -> None:
    repo = ReviewRepository(db_session)

    assert await repo.get_product_avg_rating(uuid.uuid4()) == 0.0


async def test_update_review_changes_fields(db_session) -> None:
    repo = ReviewRepository(db_session)
    created = await repo.create_review(make_data())
    await db_session.commit()

    updated = await repo.update_review(
        created.id,
        {"rating": 10, "comment": "Updated comment with enough length"},
    )
    await db_session.commit()

    assert updated is not None
    assert updated.id == created.id
    assert updated.rating == 10
    assert updated.comment == "Updated comment with enough length"


async def test_update_review_returns_none_for_unknown_id(db_session) -> None:
    repo = ReviewRepository(db_session)

    assert await repo.update_review(uuid.uuid4(), {"rating": 10}) is None


async def test_delete_review_removes_entity(db_session) -> None:
    repo = ReviewRepository(db_session)
    created = await repo.create_review(make_data())
    await db_session.commit()

    await repo.delete_review(created.id)
    await db_session.commit()

    assert await repo.get_review_by_id(created.id) is None


async def test_delete_unknown_review_does_not_raise(db_session) -> None:
    repo = ReviewRepository(db_session)

    await repo.delete_review(uuid.uuid4())
    await db_session.commit()


async def test_delete_product_reviews_removes_only_matching_product(db_session) -> None:
    repo = ReviewRepository(db_session)
    product_id = uuid.uuid4()
    await repo.create_review(make_data(product_id=product_id))
    await repo.create_review(make_data(product_id=product_id))
    remaining = await repo.create_review(make_data())
    await db_session.commit()

    await repo.delete_product_reviews(product_id)
    await db_session.commit()

    assert await repo.get_reviews_by_product_id(product_id) == []
    assert await repo.get_review_by_id(remaining.id) is not None
