import argparse
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.settings import get_settings  # noqa: E402
from app.telegram_client import TelegramBotClient  # noqa: E402


async def run(public_base_url: str | None) -> None:
    settings = get_settings()
    base_url = (public_base_url or settings.public_base_url or "").rstrip("/")
    if not base_url:
        raise SystemExit("Pass --public-base-url or set PUBLIC_BASE_URL in .env")

    webhook_url = f"{base_url}/telegram/webhook/{settings.telegram_webhook_secret}"
    client = TelegramBotClient(settings.telegram_token_value)
    try:
        result = await client.set_webhook(
            webhook_url,
            secret_token=settings.telegram_secret_token_value,
        )
        print(f"Webhook set: {webhook_url}")
        print(result)
    finally:
        await client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Register Telegram bot webhook URL.")
    parser.add_argument("--public-base-url", help="HTTPS public base URL, for example https://bot.example.com")
    args = parser.parse_args()
    asyncio.run(run(args.public_base_url))


if __name__ == "__main__":
    main()
