import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import load_channels_config  # noqa: E402
from app.settings import Settings  # noqa: E402


def main() -> None:
    settings = Settings(
        openai_api_key="dummy",
        telegram_bot_token="dummy",
        telegram_webhook_secret="dummy",
    )
    config = load_channels_config(
        path=settings.resolved_channels_config_path,
        project_root=settings.project_root,
    )
    enabled = len(config.enabled_channels)
    print(f"Config OK: {len(config.channels)} channels, {enabled} enabled")
    for channel in config.channels:
        status = "enabled" if channel.enabled else "disabled"
        print(f"- {channel.key}: {status}, cron='{channel.schedule}', prompt='{channel.prompt_file}'")


if __name__ == "__main__":
    main()
