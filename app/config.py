from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Import SAP"
    app_env: str = "development"
    secret_key: str = "change-me"
    session_cookie_name: str = "import_sap_session"
    session_max_age: int = 28800
    timezone: str = "Asia/Jakarta"

    postgres_user: str = "importsap"
    postgres_password: str = "importsap"
    postgres_db: str = "importsap"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    max_upload_size_mb: int = 100
    batch_size: int = 1000
    upload_dir: str = "uploads"
    preview_error_sample: int = 200
    record_error_sample: int = 500

    bootstrap_admin_username: str = "admin"
    bootstrap_admin_email: str = "admin@mrtjakarta.co.id"
    bootstrap_admin_password: str = "admin123"

    backup_retention_days: int = 14

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
