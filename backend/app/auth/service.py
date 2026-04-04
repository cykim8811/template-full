import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.providers.base import OAuthProvider
from app.core.security import create_access_token, create_refresh_token
from app.users.models import User
from app.users.service import UserService


class AuthService:
    def __init__(
        self, db: AsyncSession, provider: OAuthProvider, redis: aioredis.Redis
    ) -> None:
        self.db = db
        self.provider = provider
        self.redis = redis

    def get_authorization_url(self, state: str) -> str:
        return self.provider.get_authorization_url(state)

    async def authenticate(self, code: str) -> tuple[User, str, str]:
        access_token = await self.provider.exchange_code(code)
        profile = await self.provider.fetch_profile(access_token)
        user = await UserService(self.db).upsert_oauth(profile)
        jwt_token = create_access_token(user.id)
        refresh_token = await create_refresh_token(user.id, self.redis)
        return user, jwt_token, refresh_token
