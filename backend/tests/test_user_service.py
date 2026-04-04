import pytest
from app.auth.providers.base import OAuthProfile
from app.users.models import OAuthAccount
from app.users.service import UserService
from sqlalchemy import select


@pytest.fixture
def github_profile() -> OAuthProfile:
    return OAuthProfile(
        provider="github",
        provider_id="gh_123",
        email="user@example.com",
        username="testuser",
        avatar_url="https://example.com/avatar.png",
    )


async def test_upsert_oauth_creates_new_user(db_session, github_profile):
    user = await UserService(db_session).upsert_oauth(github_profile)

    assert user.email == "user@example.com"
    assert user.username == "testuser"

    result = await db_session.execute(
        select(OAuthAccount).where(OAuthAccount.user_id == user.id)
    )
    account = result.scalar_one()
    assert account.provider == "github"
    assert account.provider_id == "gh_123"


async def test_upsert_oauth_updates_existing_account(db_session, github_profile):
    user = await UserService(db_session).upsert_oauth(github_profile)

    updated = OAuthProfile(
        provider="github",
        provider_id="gh_123",
        email="user@example.com",
        username="renamed",
        avatar_url="https://example.com/new.png",
    )
    updated_user = await UserService(db_session).upsert_oauth(updated)

    assert updated_user.id == user.id
    assert updated_user.username == "renamed"
    assert updated_user.avatar_url == "https://example.com/new.png"


async def test_upsert_oauth_links_to_existing_email_user(db_session, github_profile):
    user = await UserService(db_session).upsert_oauth(github_profile)

    google_profile = OAuthProfile(
        provider="google",
        provider_id="goog_456",
        email="user@example.com",
        username="testuser",
        avatar_url=None,
    )
    linked_user = await UserService(db_session).upsert_oauth(google_profile)

    assert linked_user.id == user.id

    result = await db_session.execute(
        select(OAuthAccount).where(OAuthAccount.user_id == user.id)
    )
    accounts = result.scalars().all()
    assert {a.provider for a in accounts} == {"github", "google"}
