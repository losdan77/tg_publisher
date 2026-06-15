import logging
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

from app.config import ChannelConfig, ChannelsConfig
from app.openai_client import OpenAITextClient
from app.prompting import PromptRenderer
from app.settings import Settings
from app.telegram_client import SentMessage, TelegramBotClient

logger = logging.getLogger(__name__)


class PublishResult(BaseModel):
    channel_key: str
    channel_title: str
    reason: str
    delivered: bool
    dry_run: bool
    generated_chars: int
    message_ids: list[int] = []
    preview: str


class Publisher:
    def __init__(
        self,
        settings: Settings,
        channels_config: ChannelsConfig,
        prompt_renderer: PromptRenderer,
        openai_client: OpenAITextClient,
        telegram_client: TelegramBotClient,
    ):
        self.settings = settings
        self.channels_config = channels_config
        self.prompt_renderer = prompt_renderer
        self.openai_client = openai_client
        self.telegram_client = telegram_client
        self._last_publish_at: dict[str, datetime] = {}

    def reload_config(self, channels_config: ChannelsConfig) -> None:
        self.channels_config = channels_config

    async def publish(self, channel_key: str, reason: str, force: bool = False) -> PublishResult:
        channel = self.channels_config.get_channel(channel_key)
        if not channel.enabled and not force:
            raise ValueError(f"Channel '{channel.key}' is disabled. Use force=true for manual testing.")

        self._enforce_publish_interval(channel, force=force)
        prompt = self.prompt_renderer.render(channel, reason=reason)
        logger.info("Generating post for channel=%s reason=%s", channel.key, reason)
        post_text = await self.openai_client.generate_post(channel, prompt)

        sent_messages: list[SentMessage] = []
        dry_run = self.settings.dry_run
        if dry_run:
            logger.info("DRY_RUN enabled; not sending message to Telegram channel=%s", channel.key)
        else:
            sent_messages = await self.telegram_client.send_message(
                chat_id=channel.chat_id,
                text=post_text,
                options=channel.telegram,
            )
            self._last_publish_at[channel.key] = datetime.now(timezone.utc)
            logger.info(
                "Published channel=%s telegram_messages=%s",
                channel.key,
                [message.message_id for message in sent_messages],
            )

        return PublishResult(
            channel_key=channel.key,
            channel_title=channel.title,
            reason=reason,
            delivered=bool(sent_messages),
            dry_run=dry_run,
            generated_chars=len(post_text),
            message_ids=[message.message_id for message in sent_messages],
            preview=post_text[:700],
        )

    def list_channels(self) -> list[dict[str, Any]]:
        return [
            {
                "key": channel.key,
                "title": channel.title,
                "enabled": channel.enabled,
                "chat_id": channel.chat_id,
                "timezone": channel.timezone,
                "schedule": channel.schedule,
                "prompt_file": str(channel.prompt_file),
                "model": channel.model or self.settings.openai_default_model,
            }
            for channel in self.channels_config.channels
        ]

    def _enforce_publish_interval(self, channel: ChannelConfig, force: bool) -> None:
        if force or channel.min_seconds_between_posts == 0:
            return

        last_publish_at = self._last_publish_at.get(channel.key)
        if not last_publish_at:
            return

        seconds_since_last = (datetime.now(timezone.utc) - last_publish_at).total_seconds()
        if seconds_since_last < channel.min_seconds_between_posts:
            raise RuntimeError(
                f"Channel '{channel.key}' was published {seconds_since_last:.0f}s ago; "
                f"minimum interval is {channel.min_seconds_between_posts}s."
            )

