
import uuid
from unittest.mock import AsyncMock

from src.exceptions import ReviewNotFoundError, ReviewOwnershipError
from src.schemas import ReviewListResponseSchema, ReviewReadSchema

COMMENT = "This is a very good product"


def review_payload(review: ReviewReadSchema) -> dict:
    return review.model_dump(mode="json")


async def test_create_review(
    authenticated_client,
    current_user,
    review_service: AsyncMock,
    sample_review: ReviewReadSchema,
) -> None:
    review_service.create_review.return_value = sample_review

    response = await authenticated_client.post(
        "/reviews/",
        json={
            "product_id": str(sample_review.product_id),
            "rating": 8,
            "comment": COMMENT,
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(sample_review.id)
    review_service.create_review.assert_awaited_once()
    data, user_id, user_email = review_service.create_review.call_args.args
    assert data.product_id == sample_review.product_id
    assert user_id == current_user.id
    assert user_email == current_user.email


async def test_create_review_requires_authorization(client, review_service: AsyncMock) -> None:
    response = await client.post(
        "/reviews/",
        json={"product_id": str(uuid.uuid4()), "rating": 8, "comment": COMMENT},
    )

    assert response.status_code == 401
    review_service.create_review.assert_not_awaited()


async def test_create_review_validates_body(authenticated_client, review_service: AsyncMock) -> None:
    response = await authenticated_client.post(
        "/reviews/",
        json={"product_id": str(uuid.uuid4()), "rating": 0, "comment": "short"},
    )

    assert response.status_code == 422
    review_service.create_review.assert_not_awaited()


async def test_get_product_reviews(
    client,
    review_service: AsyncMock,
    sample_review: ReviewReadSchema,
) -> None:
    review_service.get_product_reviews.return_value = ReviewListResponseSchema(
        reviews=[sample_review],
        avg_rating=8.0,
    )

    response = await client.get(
        "/reviews/",
        params={"product_id": str(sample_review.product_id)},
    )

    assert response.status_code == 200
    assert response.json()["avg_rating"] == 8.0
    assert response.json()["reviews"][0]["id"] == str(sample_review.id)
    review_service.get_product_reviews.assert_awaited_once_with(sample_review.product_id)


async def test_get_product_reviews_requires_product_id(client, review_service: AsyncMock) -> None:
    response = await client.get("/reviews/")

    assert response.status_code == 422
    review_service.get_product_reviews.assert_not_awaited()


async def test_get_product_reviews_rejects_invalid_product_id(client, review_service: AsyncMock) -> None:
    response = await client.get("/reviews/", params={"product_id": "not-a-uuid"})

    assert response.status_code == 422
    review_service.get_product_reviews.assert_not_awaited()


async def test_get_review_by_id(
    client,
    review_service: AsyncMock,
    sample_review: ReviewReadSchema,
) -> None:
    review_service.get_review_by_id.return_value = sample_review

    response = await client.get(f"/reviews/{sample_review.id}")

    assert response.status_code == 200
    assert response.json() == review_payload(sample_review)
    review_service.get_review_by_id.assert_awaited_once_with(sample_review.id)


async def test_get_review_by_id_returns_not_found(client, review_service: AsyncMock) -> None:
    review_service.get_review_by_id.side_effect = ReviewNotFoundError()

    response = await client.get(f"/reviews/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Отзыв не найден"}


async def test_get_review_by_id_rejects_invalid_uuid(client, review_service: AsyncMock) -> None:
    response = await client.get("/reviews/not-a-uuid")

    assert response.status_code == 422
    review_service.get_review_by_id.assert_not_awaited()


async def test_delete_review(
    authenticated_client,
    current_user,
    review_service: AsyncMock,
) -> None:
    review_id = uuid.uuid4()

    response = await authenticated_client.delete(f"/reviews/{review_id}")

    assert response.status_code == 204
    review_service.delete_review.assert_awaited_once_with(
        review_id,
        current_user.id,
        current_user.email,
    )


async def test_delete_review_requires_authorization(client, review_service: AsyncMock) -> None:
    response = await client.delete(f"/reviews/{uuid.uuid4()}")

    assert response.status_code == 401
    review_service.delete_review.assert_not_awaited()


async def test_delete_review_returns_not_found(authenticated_client, review_service: AsyncMock) -> None:
    review_service.delete_review.side_effect = ReviewNotFoundError()

    response = await authenticated_client.delete(f"/reviews/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_delete_review_returns_forbidden_for_non_owner(
    authenticated_client,
    review_service: AsyncMock,
) -> None:
    review_service.delete_review.side_effect = ReviewOwnershipError()

    response = await authenticated_client.delete(f"/reviews/{uuid.uuid4()}")

    assert response.status_code == 403
    assert response.json() == {"detail": "Вы не являетесь создателем этого отзыва"}


async def test_update_review(
    authenticated_client,
    current_user,
    review_service: AsyncMock,
    sample_review: ReviewReadSchema,
) -> None:
    review_service.update_review.return_value = sample_review

    response = await authenticated_client.put(
        f"/reviews/{sample_review.id}",
        json={"rating": 9, "comment": "Updated comment with enough length"},
    )

    assert response.status_code == 200
    review_service.update_review.assert_awaited_once()
    review_id, data, user_id = review_service.update_review.call_args.args
    assert review_id == sample_review.id
    assert data.rating == 9
    assert user_id == current_user.id


async def test_update_review_validates_body(authenticated_client, review_service: AsyncMock) -> None:
    response = await authenticated_client.put(
        f"/reviews/{uuid.uuid4()}",
        json={"rating": 11, "comment": "short"},
    )

    assert response.status_code == 422
    review_service.update_review.assert_not_awaited()


async def test_update_review_returns_not_found(authenticated_client, review_service: AsyncMock) -> None:
    review_service.update_review.side_effect = ReviewNotFoundError()

    response = await authenticated_client.put(
        f"/reviews/{uuid.uuid4()}",
        json={"rating": 9, "comment": "Updated comment with enough length"},
    )

    assert response.status_code == 404


async def test_update_review_returns_forbidden_for_non_owner(
    authenticated_client,
    review_service: AsyncMock,
) -> None:
    review_service.update_review.side_effect = ReviewOwnershipError()

    response = await authenticated_client.put(
        f"/reviews/{uuid.uuid4()}",
        json={"rating": 9, "comment": "Updated comment with enough length"},
    )

    assert response.status_code == 403
