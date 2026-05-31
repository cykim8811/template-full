from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://template:template@localhost:5432/template"
    redis_url: str = "redis://localhost:6379"
    secret_key: str
    debug: bool = False

    # GitHub OAuth — optional so the backend can start without provider
    # credentials. Endpoints that require them check for presence and
    # surface a clean 503 when missing.
    github_client_id: str | None = None
    github_client_secret: str | None = None
    github_redirect_uri: str = "http://localhost:3000/api/auth/github/callback"

    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str = "http://localhost:3000/api/auth/google/callback"

    access_token_expire_minutes: int = 60  # 1 hour
    refresh_token_expire_days: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
