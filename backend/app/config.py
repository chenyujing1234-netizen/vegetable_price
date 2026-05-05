"""全局配置：通过环境变量加载"""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "dev"
    app_debug: bool = True
    app_secret_key: str = "change-me-in-prod"

    database_url: str = "postgresql+asyncpg://veg:vegpass@localhost:5432/vegdb"
    sync_database_url: str = "postgresql+psycopg://veg:vegpass@localhost:5432/vegdb"
    redis_url: str = "redis://localhost:6379/0"

    cors_origins: str = "http://localhost:3000"

    htqx_api_key: str = ""
    jisu_app_key: str = ""
    juhe_app_key: str = ""
    amap_web_key: str = ""

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
