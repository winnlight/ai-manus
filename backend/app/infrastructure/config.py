from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Model provider configuration
    api_key: str | None = None
    api_base: str = "https://api.deepseek.com/v1"

    # Model configuration
    model_name: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 2000

    # MongoDB configuration
    mongodb_uri: str = "mongodb://mongodb:27017"
    mongodb_database: str = "manus"
    mongodb_username: str | None = None
    mongodb_password: str | None = None

    # Redis configuration
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None

    # Sandbox configuration
    sandbox_address: str | None = None
    sandbox_image: str | None = None
    sandbox_name_prefix: str | None = None
    sandbox_ttl_minutes: int | None = 30
    sandbox_network: str | None = None  # Docker network bridge name
    sandbox_chrome_args: str | None = ""
    sandbox_https_proxy: str | None = None
    sandbox_http_proxy: str | None = None
    sandbox_no_proxy: str | None = None

    # Search engine configuration
    google_search_api_key: str | None = None
    google_search_engine_id: str | None = None

    # Logging configuration
    log_level: str = "INFO"

    # attachment  configuration
    storage_type: str = "mongodb"
    max_file_size: int = 200 * 1024 * 1024

    # S3 configuration (used when a storage type is s3)
    s3_bucket_name: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_region: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def validate(self):
        if not self.api_key:
            raise ValueError("API key is required")


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    settings.validate()
    return settings
