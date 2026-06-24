import logging
import html
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

from app.config import ChannelConfig, ChannelsConfig
from app.image_service import ImagePreparationError, PostImageService, PreparedImage
from app.openai_client import OpenAITextClient
from app.post_history import PostHistoryError, PostHistoryStore
from app.prompting import PromptRenderer
from app.settings import Settings
from app.telegram_client import SentMessage, TelegramApiError, TelegramBotClient

logger = logging.getLogger(__name__)


class PublishResult(BaseModel):
    channel_key: str
    channel_title: str
    reason: str
    delivered: bool
    dry_run: bool
    generated_chars: int
    image_mode: str
    image_delivered: bool = False
    image_source: str | None = None
    image_error: str | None = None
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
        post_history: PostHistoryStore,
        image_service: PostImageService,
    ):
        self.settings = settings
        self.channels_config = channels_config
        self.prompt_renderer = prompt_renderer
        self.openai_client = openai_client
        self.telegram_client = telegram_client
        self.post_history = post_history
        self.image_service = image_service
        self._last_publish_at: dict[str, datetime] = {}

    def reload_config(self, channels_config: ChannelsConfig) -> None:
        self.channels_config = channels_config

    async def publish(self, channel_key: str, reason: str, force: bool = False) -> PublishResult:
        channel = self.channels_config.get_channel(channel_key)
        if not channel.enabled and not force:
            raise ValueError(f"Channel '{channel.key}' is disabled. Use force=true for manual testing.")

        self._enforce_publish_interval(channel, force=force)
        history = None
        if channel.history_enabled:
            history = self.post_history.recent(channel.key, channel.history_posts_limit)
        prompt = self.prompt_renderer.render(channel, reason=reason, post_history=history)
        logger.info("Generating post for channel=%s reason=%s", channel.key, reason)
        post_text = await self.openai_client.generate_post(channel, prompt)

        prepared_image: PreparedImage | None = None
        image_error: str | None = None
        if channel.image.mode != "none":
            try:
                prepared_image = await self.image_service.prepare(channel, post_text)
            except ImagePreparationError as exc:
                if not channel.image.fallback_to_text:
                    raise
                image_error = str(exc)
                logger.exception("Image preparation failed; publishing text only channel=%s", channel.key)

        sent_messages: list[SentMessage] = []
        image_delivered = False
        dry_run = self.settings.dry_run
        if dry_run:
            logger.info("DRY_RUN enabled; not sending message to Telegram channel=%s", channel.key)
        else:
            if prepared_image is not None:
                try:
                    sent_messages, image_delivered = await self._send_with_image(
                        channel,
                        post_text,
                        prepared_image,
                    )
                except TelegramApiError as exc:
                    if not channel.image.fallback_to_text:
                        raise
                    image_error = str(exc)
                    logger.exception("Photo delivery failed; publishing text only channel=%s", channel.key)
                    sent_messages = await self.telegram_client.send_message(
                        chat_id=channel.chat_id,
                        text=post_text,
                        options=channel.telegram,
                    )
            else:
                sent_messages = await self.telegram_client.send_message(
                    chat_id=channel.chat_id,
                    text=post_text,
                    options=channel.telegram,
                )
            self._last_publish_at[channel.key] = datetime.now(timezone.utc)
            try:
                self.post_history.add(
                    channel_key=channel.key,
                    text=post_text,
                    message_ids=[message.message_id for message in sent_messages],
                    reason=reason,
                )
            except PostHistoryError:
                logger.exception("Published post but failed to save history channel=%s", channel.key)
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
            image_mode=channel.image.mode,
            image_delivered=image_delivered,
            image_source=prepared_image.source if image_delivered and prepared_image else None,
            image_error=image_error,
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
                "history_enabled": channel.history_enabled,
                "history_posts_limit": channel.history_posts_limit,
                "image_mode": channel.image.mode,
            }
            for channel in self.channels_config.channels
        ]

    async def _send_with_image(
        self,
        channel: ChannelConfig,
        post_text: str,
        image: PreparedImage,
    ) -> tuple[list[SentMessage], bool]:
        caption = photo_caption(post_text, image, channel.telegram.parse_mode)
        photo_message = await self.telegram_client.send_photo(
            chat_id=channel.chat_id,
            photo=image.content,
            filename=image.filename,
            mime_type=image.mime_type,
            caption=caption,
            options=channel.telegram,
        )
        sent_messages = [photo_message]
        if caption is None or not caption_includes_post(caption, post_text):
            sent_messages.extend(
                await self.telegram_client.send_message(
                    chat_id=channel.chat_id,
                    text=post_text,
                    options=channel.telegram,
                )
            )
        return sent_messages, True

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


def photo_caption(
    post_text: str,
    image: PreparedImage,
    parse_mode: str | None = None,
    limit: int = 1024,
) -> str | None:
    credit = format_photo_credit(image, parse_mode)
    candidate = f"{post_text}\n\n{credit}" if credit else post_text
    if len(candidate) <= limit:
        return candidate
    if credit and len(credit) <= limit:
        return credit
    return None


def caption_includes_post(caption: str, post_text: str) -> bool:
    return caption.startswith(post_text)


def format_photo_credit(image: PreparedImage, parse_mode: str | None) -> str | None:
    if not image.credit:
        return None
    value = f"{image.credit}: {image.source_url}" if image.source_url else image.credit
    if parse_mode == "HTML":
        return html.escape(value, quote=False)
    if parse_mode == "MarkdownV2":
        for char in r"_*[]()~`>#+-=|{}.!":
            value = value.replace(char, f"\\{char}")
    elif parse_mode == "Markdown":
        for char in r"_*[]`":
            value = value.replace(char, f"\\{char}")
    return value
