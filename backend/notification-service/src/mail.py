
from email.message import EmailMessage

from aiosmtplib import send

from src.config import settings


async def send_welcome_email(username: str, to_email: str) -> None:
    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to_email
    message["Subject"] = "Добро пожаловать в Market!"

    html_content = f"""
        <html>
            <body>
                <h2>Привет, {username}!</h2>

                <p>
                    Спасибо за регистрацию в нашем маркетплейсе
                    Market Microservices.
                </p>

                <p>
                    Ваш аккаунт успешно создан и готов к работе.
                </p>

                <br>

                <small>
                    Это автоматическое письмо, отвечать на него не нужно.
                </small>
            </body>
        </html>
    """
    message.set_content(html_content, subtype="html")

    try:
        await send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            use_tls=False,
            start_tls=False
        )
    except Exception:
        pass
