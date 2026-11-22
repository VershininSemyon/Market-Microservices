
from email.message import EmailMessage
from unittest.mock import AsyncMock

import pytest

import src.mail as mail_module
from src.config import settings
from src.mail import (
    _send_email,
    send_account_deleted_email,
    send_order_created_email,
    send_product_created_email,
    send_product_deleted_email,
    send_review_created_email,
    send_review_deleted_email,
    send_welcome_email,
)


@pytest.fixture
def send_mock(monkeypatch) -> AsyncMock:
    mock = AsyncMock()
    monkeypatch.setattr(mail_module, "send", mock)
    return mock


def sent_message(send_mock: AsyncMock) -> EmailMessage:
    return send_mock.await_args.args[0]


async def test_send_email_builds_message_and_uses_smtp_settings(send_mock: AsyncMock) -> None:
    await _send_email(
        subject="Test subject",
        html_content="<html><body>Hello</body></html>",
        to_email="alice@example.com",
    )

    message = sent_message(send_mock)
    assert isinstance(message, EmailMessage)
    assert message["From"] == settings.SMTP_FROM
    assert message["To"] == "alice@example.com"
    assert message["Subject"] == "Test subject"
    assert message.get_content_type() == "text/html"
    assert "Hello" in message.get_content()

    send_mock.assert_awaited_once_with(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        use_tls=False,
        start_tls=False,
    )


@pytest.mark.parametrize(
    ("sender", "kwargs", "expected_subject", "expected_fragment"),
    [
        (
            send_welcome_email,
            {"username": "alice", "to_email": "alice@example.com"},
            "Добро пожаловать в Market!",
            "alice",
        ),
        (
            send_account_deleted_email,
            {"to_email": "alice@example.com"},
            "Вы удалили аккаунт",
            "Вы удалили аккаунт",
        ),
        (
            send_product_created_email,
            {"product_name": "apple", "to_email": "alice@example.com"},
            "Добавление продукта",
            "apple",
        ),
        (
            send_product_deleted_email,
            {"product_name": "apple", "to_email": "alice@example.com"},
            "Удаление продукта",
            "apple",
        ),
        (
            send_review_created_email,
            {"product_id": "product-1", "to_email": "alice@example.com"},
            "Добавление отзыва",
            "product-1",
        ),
        (
            send_review_deleted_email,
            {"product_id": "product-1", "to_email": "alice@example.com"},
            "Удаление отзыва",
            "product-1",
        ),
        (
            send_order_created_email,
            {
                "total_price": 20.5,
                "total_amount": 2,
                "to_email": "alice@example.com",
            },
            "Создание заказа",
            "20.5",
        ),
    ],
)
async def test_sender_builds_expected_email(
    send_mock: AsyncMock,
    sender,
    kwargs: dict,
    expected_subject: str,
    expected_fragment: str,
) -> None:
    await sender(**kwargs)

    message = sent_message(send_mock)
    assert message["From"] == settings.SMTP_FROM
    assert message["To"] == kwargs["to_email"]
    assert message["Subject"] == expected_subject
    assert expected_fragment in message.get_content()
    send_mock.assert_awaited_once()


async def test_order_email_contains_amount(send_mock: AsyncMock) -> None:
    await send_order_created_email(
        total_price=99.9,
        total_amount=7,
        to_email="alice@example.com",
    )

    content = sent_message(send_mock).get_content()
    assert "99.9" in content
    assert "7" in content


async def test_sender_propagates_smtp_error(send_mock: AsyncMock) -> None:
    send_mock.side_effect = RuntimeError("smtp is down")

    with pytest.raises(RuntimeError):
        await send_welcome_email(username="alice", to_email="alice@example.com")
