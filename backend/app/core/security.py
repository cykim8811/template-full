import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt
import redis.asyncio as aioredis

from app.core.config import settings
from app.exceptions import InvalidTokenError

ALGORITHM = "HS256"
_REFRESH_KEY_PREFIX = "refresh:"


def create_access_token(user_id: uuid.UUID) -> str:
    expire = datetime.now(UTC) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    return jwt.encode(
        {"sub": str(user_id), "exp": expire}, settings.secret_key, algorithm=ALGORITHM
    )


def decode_access_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return uuid.UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise InvalidTokenError from None


async def create_refresh_token(user_id: uuid.UUID, redis: aioredis.Redis) -> str:
    token = secrets.token_urlsafe(32)
    ttl = settings.refresh_token_expire_days * 86400
    await redis.set(f"{_REFRESH_KEY_PREFIX}{token}", str(user_id), ex=ttl)
    return token


async def verify_and_rotate_refresh_token(
    token: str, redis: aioredis.Redis
) -> tuple[uuid.UUID, str]:
    key = f"{_REFRESH_KEY_PREFIX}{token}"
    user_id_str = await redis.getdel(key)  # atomic: prevents concurrent token reuse
    if not user_id_str:
        raise InvalidTokenError
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise InvalidTokenError from None
    new_token = secrets.token_urlsafe(32)
    ttl = settings.refresh_token_expire_days * 86400
    await redis.set(f"{_REFRESH_KEY_PREFIX}{new_token}", str(user_id), ex=ttl)
    return user_id, new_token
