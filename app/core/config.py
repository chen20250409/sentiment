from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "sentiment-nlp"
    app_version: str = "1.0.0"

    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "nlp"
    db_password: str = ""
    db_name: str = "sentiment"
    # 可整体覆盖连接串（测试用 SQLite 时设置）
    database_url: str | None = None

    log_level: str = "INFO"

    # 情感打分参数（可在 .env 调参）
    pos_threshold: float = 0.5
    neg_threshold: float = -0.5
    conf_scale: float = 1.5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def db_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"mysql+aiomysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
