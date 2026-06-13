from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    META_VERIFY_TOKEN: str = "default_token"
    META_PAGE_ACCESS_TOKEN: str = "default_page_token"
    META_APP_SECRET: str = "default_app_secret"
    OPENROUTER_API_KEY: str = "default_or_key"
    DEEPSEEK_API_KEY: str = "default_ds_key"
    OPENAI_API_KEY: str = "default_oa_key"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache()
def get_settings():
    return Settings()
