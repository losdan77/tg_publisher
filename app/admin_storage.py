from pathlib import Path
import os

from app.config import ChannelConfig, ChannelsConfig, load_channels_config, resolve_prompt_path, save_channels_config
from app.settings import Settings


class AdminStorageError(ValueError):
    pass


def load_live_config(settings: Settings) -> ChannelsConfig:
    return load_channels_config(
        path=settings.resolved_channels_config_path,
        project_root=settings.project_root,
    )


def save_live_config(settings: Settings, config: ChannelsConfig) -> None:
    try:
        save_channels_config(settings.resolved_channels_config_path, config)
    except OSError as exc:
        raise AdminStorageError(
            storage_error_message("write config file", settings.resolved_channels_config_path, exc)
        ) from exc


def upsert_channel(
    settings: Settings,
    channel: ChannelConfig,
    original_key: str | None = None,
) -> ChannelsConfig:
    prompt_path = assert_safe_prompt_path(settings.project_root, str(channel.prompt_file))
    if not prompt_path.exists():
        raise AdminStorageError(f"Prompt file does not exist: {channel.prompt_file}")

    config = load_live_config(settings)
    replace_key = original_key or channel.key
    channels = []
    replaced = False

    for existing in config.channels:
        if existing.key == replace_key:
            channels.append(channel)
            replaced = True
        else:
            channels.append(existing)

    if not replaced:
        channels.append(channel)

    new_config = ChannelsConfig(channels=channels)
    save_live_config(settings, new_config)
    return new_config


def delete_channel(settings: Settings, channel_key: str) -> ChannelsConfig:
    config = load_live_config(settings)
    channels = [channel for channel in config.channels if channel.key != channel_key]
    if len(channels) == len(config.channels):
        raise AdminStorageError(f"Channel '{channel_key}' does not exist")

    new_config = ChannelsConfig(channels=channels)
    save_live_config(settings, new_config)
    return new_config


def list_prompt_files(project_root: Path) -> list[str]:
    prompts_dir = project_root / "prompts"
    if not prompts_dir.exists():
        return []
    return [
        prompt_path.relative_to(project_root).as_posix()
        for prompt_path in sorted(prompts_dir.rglob("*.md"))
        if prompt_path.is_file()
    ]


def read_prompt(project_root: Path, prompt_file: str) -> str:
    path = assert_safe_prompt_path(project_root, prompt_file)
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AdminStorageError(storage_error_message("read prompt file", path, exc)) from exc


def write_prompt(project_root: Path, prompt_file: str, content: str) -> str:
    path = assert_safe_prompt_path(project_root, prompt_file)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    except OSError as exc:
        raise AdminStorageError(storage_error_message("write prompt file", path, exc)) from exc
    return path.relative_to(project_root).as_posix()


def storage_status(settings: Settings) -> dict[str, object]:
    config_path = settings.resolved_channels_config_path
    prompts_dir = settings.project_root / "prompts"

    return {
        "config_path": str(config_path),
        "config_parent_writable": is_writable_directory(config_path.parent),
        "config_file_writable": is_writable_file(config_path),
        "prompts_dir": str(prompts_dir),
        "prompts_dir_writable": is_writable_directory(prompts_dir),
    }


def is_writable_directory(path: Path) -> bool:
    return path.exists() and path.is_dir() and os.access(path, os.W_OK)


def is_writable_file(path: Path) -> bool:
    if path.exists():
        return path.is_file() and os.access(path, os.W_OK)
    return is_writable_directory(path.parent)


def storage_error_message(action: str, path: Path, exc: OSError) -> str:
    return (
        f"Cannot {action}: {path}. {exc.strerror or exc}. "
        "On VPS, check ownership of ./data/config and ./data/prompts. "
        "They must be writable by APP_UID:APP_GID from .env."
    )


def assert_safe_prompt_path(project_root: Path, prompt_file: str) -> Path:
    normalized = _normalize_prompt_file(prompt_file)
    path = resolve_prompt_path(project_root, Path(normalized)).resolve()
    prompts_dir = (project_root / "prompts").resolve()

    if not path.is_relative_to(prompts_dir):
        raise AdminStorageError("Prompt file must be inside prompts/")
    if path.suffix.lower() != ".md":
        raise AdminStorageError("Prompt file must have .md extension")

    return path


def _normalize_prompt_file(prompt_file: str) -> str:
    value = prompt_file.replace("\\", "/").strip().lstrip("/")
    if not value:
        raise AdminStorageError("Prompt file is required")
    if value.startswith("../") or "/../" in value:
        raise AdminStorageError("Prompt file cannot contain '..'")
    if not value.startswith("prompts/"):
        value = f"prompts/{value}"
    return value
