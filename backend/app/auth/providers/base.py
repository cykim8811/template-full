from dataclasses import dataclass
from typing import Protocol


@dataclass
class OAuthProfile:
    provider: str
    provider_id: str
    email: str
    username: str
    avatar_url: str | None


class OAuthProvider(Protocol):
    def get_authorization_url(self, state: str) -> str: ...
    async def exchange_code(self, code: str) -> str: ...
    async def fetch_profile(self, access_token: str) -> OAuthProfile: ...
