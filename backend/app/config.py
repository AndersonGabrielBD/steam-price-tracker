from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://tracker:tracker@localhost:5432/price_tracker"
    redis_url: str = "redis://localhost:6379/0"
    steam_api_base_url: str = "https://store.steampowered.com/api"
    steam_region_cc: str = "br"
    steam_region_lang: str = "portuguese"
    price_check_interval_minutes: int = 20
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
