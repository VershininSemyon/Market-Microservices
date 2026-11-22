
import os

os.environ.update(
    {
        "RABBITMQ_USER": "guest",
        "RABBITMQ_PASSWORD": "guest",
        "RABBITMQ_HOST": "localhost",
        "RABBITMQ_PORT": "5672",
        "SMTP_HOST": "localhost",
        "SMTP_PORT": "1025",
        "SMTP_FROM": "noreply@market.test",
    }
)
