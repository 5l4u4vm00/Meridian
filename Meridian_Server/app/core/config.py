from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Meridian API"
    database_url: str = "postgresql+psycopg://meridian:meridian@localhost:5432/meridian"

    jwt_secret: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7

    session_secret: str = "dev-insecure-change-me-too"
    oauth_redirect_base: str = "http://localhost:8000"
    cors_origins: list[str] = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]

    initial_admin_email: str | None = None

    google_client_id: str | None = None
    google_client_secret: str | None = None
    github_client_id: str | None = None
    github_client_secret: str | None = None


settings = Settings()
