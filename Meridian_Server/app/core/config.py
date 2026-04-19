from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Meridian API"
    database_url: str = "postgresql+psycopg://meridian:meridian@localhost:5432/meridian"


settings = Settings()
