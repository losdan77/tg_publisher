from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class TelegramOptions(BaseModel):
    parse_mode: Literal["HTML", "Markdown", "MarkdownV2"] | None = "HTML"
    disable_web_page_preview: bool = True
    protect_content: bool = False


class ChannelConfig(BaseModel):
    key: str = Field(min_length=2, max_length=64)
    title: str = Field(min_length=1, max_length=160)
    chat_id: str | int
    enabled: bool = True
    timezone: str = "Europe/Moscow"
    schedule: str = Field(description="Five-field crontab expression: minute hour day month weekday")
    prompt_file: Path
    model: str | None = None
    max_output_tokens: int = Field(default=1200, ge=100, le=8000)
    temperature: float | None = Field(default=None, ge=0, le=2)
    reasoning_effort: Literal["minimal", "low", "medium", "high"] | None = None
    text_verbosity: Literal["low", "medium", "high"] | None = None
    telegram: TelegramOptions = Field(default_factory=TelegramOptions)
    min_seconds_between_posts: int = Field(default=300, ge=0)
    context: dict[str, Any] = Field(default_factory=dict)

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_-")
        if any(char not in allowed for char in value):
            raise ValueError("key must contain only lowercase latin letters, digits, '_' or '-'")
        if value[0] in "_-" or value[-1] in "_-":
            raise ValueError("key must start and end with a letter or digit")
        return value

    @field_validator("schedule")
    @classmethod
    def validate_schedule(cls, value: str) -> str:
        parts = value.split()
        if len(parts) != 5:
            raise ValueError("schedule must be a five-field crontab expression")
        return value


class ChannelsConfig(BaseModel):
    channels: list[ChannelConfig] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_keys(self) -> "ChannelsConfig":
        keys = [channel.key for channel in self.channels]
        duplicates = sorted({key for key in keys if keys.count(key) > 1})
        if duplicates:
            raise ValueError(f"duplicate channel keys: {', '.join(duplicates)}")
        return self

    def get_channel(self, key: str) -> ChannelConfig:
        for channel in self.channels:
            if channel.key == key:
                return channel
        raise KeyError(f"Unknown channel: {key}")

    @property
    def enabled_channels(self) -> list[ChannelConfig]:
        return [channel for channel in self.channels if channel.enabled]


def load_channels_config(path: Path, project_root: Path) -> ChannelsConfig:
    if not path.exists():
        raise FileNotFoundError(f"Channels config not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file) or {}

    config = ChannelsConfig.model_validate(raw)
    _validate_prompt_files(config, project_root)
    return config


def save_channels_config(path: Path, config: ChannelsConfig) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "channels": [
            channel.model_dump(mode="json", exclude_none=True)
            for channel in config.channels
        ]
    }
    with path.open("w", encoding="utf-8", newline="\n") as file:
        yaml.safe_dump(
            data,
            file,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )


def resolve_prompt_path(project_root: Path, prompt_file: Path) -> Path:
    if prompt_file.is_absolute():
        return prompt_file
    return project_root / prompt_file


def _validate_prompt_files(config: ChannelsConfig, project_root: Path) -> None:
    missing = []
    for channel in config.channels:
        prompt_path = resolve_prompt_path(project_root, channel.prompt_file)
        if not prompt_path.exists():
            missing.append(f"{channel.key}: {prompt_path}")
    if missing:
        raise FileNotFoundError("Prompt files not found:\n" + "\n".join(missing))
