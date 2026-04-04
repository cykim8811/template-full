import secrets

import redis.asyncio as aioredis
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.providers.github import GitHubOAuthProvider
from app.auth.providers.google import GoogleOAuthProvider
from app.auth.schemas import LogoutRequest, RefreshRequest, TokenResponse
from app.auth.service import AuthService
from app.core.config import settings
from app.core.security import (
    _REFRESH_KEY_PREFIX,
    create_access_token,
    verify_and_rotate_refresh_token,
)
from app.deps import get_db, get_redis
from app.exceptions import InvalidTokenError, UserNotFoundError
from app.users.service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])

_OAUTH_STATE_COOKIE = "oauth_state"
_OAUTH_STATE_TTL = 600  # 10 minutes


def _make_auth_service(provider_cls):
    def get_auth_service(
        db: AsyncSession = Depends(get_db),
        redis: aioredis.Redis = Depends(get_redis),
    ) -> AuthService:
        return AuthService(db, provider_cls(), redis)

    return get_auth_service


get_github_auth_service = _make_auth_service(GitHubOAuthProvider)


def _login_response(
    authorization_url: str, state: str, secure: bool
) -> RedirectResponse:
    response = RedirectResponse(authorization_url)
    response.set_cookie(
        key=_OAUTH_STATE_COOKIE,
        value=state,
        max_age=_OAUTH_STATE_TTL,
        httponly=True,
        samesite="lax",
        secure=secure,
    )
    return response


@router.get("/github")
async def github_login(
    request: Request, service: AuthService = Depends(get_github_auth_service)
) -> RedirectResponse:
    state = secrets.token_urlsafe(32)
    return _login_response(
        service.get_authorization_url(state), state, secure=not settings.debug
    )


async def _oauth_callback(
    code: str, state: str, service: AuthService, oauth_state: str | None
) -> TokenResponse:
    if not oauth_state or not secrets.compare_digest(state, oauth_state):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid OAuth state"
        )
    _, jwt_token, refresh_token = await service.authenticate(code)
    return TokenResponse(
        access_token=jwt_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get("/github/callback", response_model=TokenResponse)
async def github_callback(
    request: Request,
    code: str,
    state: str,
    service: AuthService = Depends(get_github_auth_service),
    oauth_state: str | None = Cookie(default=None),
) -> TokenResponse:
    return await _oauth_callback(code, state, service, oauth_state)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    body: RefreshRequest,
    redis: aioredis.Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        user_id, new_refresh_token = await verify_and_rotate_refresh_token(
            body.refresh_token, redis
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from None
    try:
        await UserService(db).get_by_id(user_id)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from None
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=new_refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/logout")
async def logout(
    body: LogoutRequest,
    redis: aioredis.Redis = Depends(get_redis),
) -> dict:
    await redis.delete(f"{_REFRESH_KEY_PREFIX}{body.refresh_token}")
    return {"ok": True}


if settings.google_client_id and settings.google_client_secret:
    get_google_auth_service = _make_auth_service(GoogleOAuthProvider)

    @router.get("/google")
    async def google_login(
        request: Request, service: AuthService = Depends(get_google_auth_service)
    ) -> RedirectResponse:
        state = secrets.token_urlsafe(32)
        return _login_response(
            service.get_authorization_url(state), state, secure=not settings.debug
        )

    @router.get("/google/callback", response_model=TokenResponse)
    async def google_callback(
        request: Request,
        code: str,
        state: str,
        service: AuthService = Depends(get_google_auth_service),
        oauth_state: str | None = Cookie(default=None),
    ) -> TokenResponse:
        return await _oauth_callback(code, state, service, oauth_state)
