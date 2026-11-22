
from src.config import settings


def test_amqp_url_is_built_from_connection_settings() -> None:
    assert settings.amqp_url == "amqp://guest:guest@localhost:5672/"


def test_smtp_settings_are_loaded() -> None:
    assert settings.SMTP_HOST == "localhost"
    assert settings.SMTP_PORT == 1025
    assert settings.SMTP_FROM == "noreply@market.test"


def test_queue_and_routing_key_defaults() -> None:
    assert settings.USER_EVENTS_EXCHANGE_NAME == "user-events-exchange"
    assert settings.USER_CREATED_QUEUE_NAME == "notification.user-created-queue"
    assert settings.USER_CREATED_ROUTING_KEY == "user.created"

    assert settings.PRODUCTS_EVENTS_EXCHANGE_NAME == "products-events-exchange"
    assert settings.PRODUCT_CREATED_QUEUE_NAME == "notification.product-created-queue"
    assert settings.PRODUCT_CREATED_ROUTING_KEY == "product.created"

    assert settings.REVIEWS_EVENTS_EXCHANGE_NAME == "reviews-events-exchange"
    assert settings.REVIEW_CREATED_QUEUE_NAME == "notification.review-created-queue"
    assert settings.REVIEW_CREATED_ROUTING_KEY == "review.created"

    assert settings.ORDERS_EVENTS_EXCHANGE_NAME == "orders-events-exchange"
    assert settings.ORDER_CREATED_QUEUE_NAME == "notification.order-created-queue"
    assert settings.ORDER_CREATED_ROUTING_KEY == "order.created"

    assert settings.DLX_EXCHANGE_NAME == "notification-dlx"
    assert settings.DLQ_NAME == "notification-dlq"
