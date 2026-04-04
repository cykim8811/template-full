import re

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client, OAuth2Client

from app.auth.providers.base import OAuthProfile
from app.core.config import settings
from app.exceptions import OAuthError


class GoogleOAuthProvider:
    _AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    _TOKEN_URL = "https://oauth2.googleapis.com/token"
    _USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    _SCOPE = "openid email profile"

    def get_authorization_url(self, state: str) -> str:
        client = OAuth2Client(
            client_id=settings.google_client_id,
            redirect_uri=settings.google_redirect_uri,
            scope=self._SCOPE,
        )
        url, _ = client.create_authorization_url(
            self._AUTHORIZATION_URL,
            state=state,
            access_type="offline",
        )
        return url

    async def exchange_code(self, code: str) -> str:
        async with AsyncOAuth2Client(
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            redirect_uri=settings.google_redirect_uri,
        ) as client:
            token = await client.fetch_token(self._TOKEN_URL, code=code)
        access_token = token.get("access_token")
        if not access_token:
            raise OAuthError("No access token in Google response")
        return access_token

    async def fetch_profile(self, access_token: str) -> OAuthProfile:
        async with AsyncOAuth2Client(
            token={"access_token": access_token, "token_type": "bearer"},
        ) as client:
            response = await client.get(self._USERINFO_URL)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise OAuthError("Failed to fetch Google profile") from e
        data = response.json()
        email = data.get("email")
        if not email:
            raise OAuthError("Google account has no email")
        raw = data.get("name") or email.split("@")[0]
        username = re.sub(r"[^\w]", "_", raw).strip("_") or email.split("@")[0]
        return OAuthProfile(
            provider="google",
            provider_id=str(data["id"]),
            email=email,
            username=username,
            avatar_url=data.get("picture"),
        )
