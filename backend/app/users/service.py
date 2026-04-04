import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.providers.base import OAuthProfile
from app.exceptions import UsernameAlreadyTakenError, UserNotFoundError
from app.users.models import OAuthAccount, User


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise UserNotFoundError(user_id)
        return user

    async def _unique_username(self, base: str) -> str:
        candidate = base
        n = 1
        while True:
            exists = await self.db.scalar(
                select(User.id).where(User.username == candidate)
            )
            if not exists:
                return candidate
            candidate = f"{base}_{n}"
            n += 1

    async def update_user(self, user: User, username: str | None, avatar_url: str | None) -> User:
        if username is not None and username != user.username:
            exists = await self.db.scalar(select(User.id).where(User.username == username))
            if exists:
                raise UsernameAlreadyTakenError(username)
            user.username = username
        if avatar_url is not None:
            user.avatar_url = avatar_url
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def upsert_oauth(self, profile: OAuthProfile) -> User:
        # 1. Look up existing OAuth account
        result = await self.db.execute(
            select(OAuthAccount)
            .where(
                OAuthAccount.provider == profile.provider,
                OAuthAccount.provider_id == profile.provider_id,
            )
            .options(selectinload(OAuthAccount.user))
        )
        account = result.scalar_one_or_none()
        if account:
            if account.user.username != profile.username:
                account.user.username = await self._unique_username(profile.username)
            account.user.avatar_url = profile.avatar_url
            await self.db.commit()
            return account.user

        # 2. Find or create user by email
        try:
            result = await self.db.execute(
                select(User).where(User.email == profile.email)
            )
            user = result.scalar_one_or_none()
            if not user:
                username = await self._unique_username(profile.username)
                user = User(
                    email=profile.email,
                    username=username,
                    avatar_url=profile.avatar_url,
                )
                self.db.add(user)
                await self.db.flush()

            # 3. Link OAuth account
            account = OAuthAccount(
                user_id=user.id,
                provider=profile.provider,
                provider_id=profile.provider_id,
            )
            self.db.add(account)
            await self.db.commit()
            return user
        except IntegrityError:
            await self.db.rollback()
            # 동시 요청으로 인한 race condition — 이미 생성된 계정을 재조회
            result = await self.db.execute(
                select(OAuthAccount)
                .where(
                    OAuthAccount.provider == profile.provider,
                    OAuthAccount.provider_id == profile.provider_id,
                )
                .options(selectinload(OAuthAccount.user))
            )
            account = result.scalar_one_or_none()
            if account:
                return account.user
            raise
