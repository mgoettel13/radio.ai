from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./npr_news.db"

    # Security
    secret_key: str = "change-me-in-production"

    # API Keys
    perplexity_api_key: str = ""
    speechify_api_key: str = ""

    # App Settings
    app_port: int = 8000
    app_host: str = "0.0.0.0"
    rss_refresh_minutes: int = 10
    max_articles: int = 20
    npr_feed_url: str = "https://feeds.npr.org/1002/rss.xml"

    # CORS
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
