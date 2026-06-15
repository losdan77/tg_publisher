from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["local", "production", "test"] = "local"
    log_level: str = "INFO"
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[1])

    openai_api_key: SecretStr
    openai_default_model: str = "gpt-5.5"
    openai_timeout_seconds: float = 60.0

    telegram_bot_token: SecretStr
    telegram_webhook_secret: str
    telegram_webhook_secret_token: SecretStr | None = None
    admin_api_token: SecretStr | None = None
    admin_telegram_user_ids: str = ""

    channels_config_path: Path = Path("config/channels.yaml")
    enable_scheduler: bool = True
    dry_run: bool = False
    public_base_url: str | None = None

    def resolve_path(self, value: Path) -> Path:
        if value.is_absolute():
            return value
        return self.project_root / value

    @property
    def resolved_channels_config_path(self) -> Path:
        return self.resolve_path(self.channels_config_path)

    @property
    def telegram_token_value(self) -> str:
        return self.telegram_bot_token.get_secret_value()

    @property
    def openai_key_value(self) -> str:
        return self.openai_api_key.get_secret_value()

    @property
    def admin_api_token_value(self) -> str | None:
        if self.admin_api_token is None:
            return None
        return self.admin_api_token.get_secret_value()

    @property
    def telegram_secret_token_value(self) -> str | None:
        if self.telegram_webhook_secret_token is None:
            return None
        return self.telegram_webhook_secret_token.get_secret_value()

    @property
    def admin_telegram_user_id_set(self) -> set[int]:
        if not self.admin_telegram_user_ids.strip():
            return set()
        return {
            int(item.strip())
            for item in self.admin_telegram_user_ids.split(",")
            if item.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
