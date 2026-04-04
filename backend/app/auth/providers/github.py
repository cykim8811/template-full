import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client, OAuth2Client

from app.auth.providers.base import OAuthProfile
from app.core.config import settings
from app.exceptions import OAuthError


class GitHubOAuthProvider:
    _AUTHORIZATION_URL = "https://github.com/login/oauth/authorize"
    _TOKEN_URL = "https://github.com/login/oauth/access_token"
    _USERINFO_URL = "https://api.github.com/user"
    _SCOPE = "read:user user:email"

    def get_authorization_url(self, state: str) -> str:
        client = OAuth2Client(
            client_id=settings.github_client_id,
            redirect_uri=settings.github_redirect_uri,
            scope=self._SCOPE,
        )
        url, _ = client.create_authorization_url(self._AUTHORIZATION_URL, state=state)
        return url

    async def exchange_code(self, code: str) -> str:
        async with AsyncOAuth2Client(
            client_id=settings.github_client_id,
            client_secret=settings.github_client_secret,
            redirect_uri=settings.github_redirect_uri,
        ) as client:
            token = await client.fetch_token(
                self._TOKEN_URL,
                code=code,
                headers={"Accept": "application/json"},
            )
        access_token = token.get("access_token")
        if not access_token:
            raise OAuthError("No access token in GitHub response")
        return access_token

    async def _fetch_primary_email(self, client: AsyncOAuth2Client) -> str | None:
        response = await client.get(
            "https://api.github.com/user/emails",
            headers={"Accept": "application/json"},
        )
        if not response.is_success:
            return None
        emails = response.json()
        for entry in emails:
            if entry.get("primary") and entry.get("verified"):
                return entry.get("email")
        return None

    async def fetch_profile(self, access_token: str) -> OAuthProfile:
        async with AsyncOAuth2Client(
            token={"access_token": access_token, "token_type": "bearer"},
        ) as client:
            response = await client.get(
                self._USERINFO_URL,
                headers={"Accept": "application/json"},
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise OAuthError("Failed to fetch GitHub profile") from e
            data = response.json()
            email = data.get("email")
            if not email:
                email = await self._fetch_primary_email(client)
            email = email or f"{data['login']}@users.noreply.github.com"
        return OAuthProfile(
            provider="github",
            provider_id=str(data["id"]),
            email=email,
            username=data["login"],
            avatar_url=data.get("avatar_url"),
        )
