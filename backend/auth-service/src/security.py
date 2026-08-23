
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from config import settings
from exceptions import InvalidTokenError, TokenExpiredError


def _create_token(data: dict, token_type: str, lifetime: timedelta) -> str:
    payload = {
        **data,
        "token_type": token_type,
        "exp": datetime.now(timezone.utc) + lifetime
    }
    return jwt.encode(
        payload=payload,
        algorithm=settings.JWT_ALGORITHM,
        key=settings.JWT_PRIVATE_KEY
    )

def create_access_token(data: dict) -> str:
    return _create_token(
        data=data,
        token_type="access",
        lifetime=timedelta(minutes=settings.ACCESS_TOKEN_LIFETIME_MINUTES)
    )

def create_refresh_token(data: dict) -> str:
    return _create_token(
        data=data,
        token_type="refresh",
        lifetime=timedelta(days=settings.REFRESH_TOKEN_LIFETIME_DAYS)
    )

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            jwt=token,
            algorithms=[settings.JWT_ALGORITHM],
            key=settings.JWT_PUBLIC_KEY
        )
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError()
    except jwt.InvalidTokenError:
        raise InvalidTokenError()


def hash_password(password: str) -> str:
    prepared_password = f"{password}{settings.PASSWORD_SALT}".encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(prepared_password, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    prepared_password = f"{plain_password}{settings.PASSWORD_SALT}".encode('utf-8')
    return bcrypt.checkpw(prepared_password, hashed_password.encode('utf-8'))
