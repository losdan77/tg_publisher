from pathlib import Path

import pytest

from app.config import ChannelConfig, ChannelsConfig
from app.image_service import ImagePreparationError, PreparedImage
from app.post_history import PostHistoryStore
from app.publisher import Publisher
from app.settings import Settings
from app.telegram_client import SentMessage


class FakePromptRenderer:
    def __init__(self) -> None:
        self.received_history = None

    def render(self, channel, reason, post_history=None):
        self.received_history = post_history
        return "rendered prompt"


class FakeOpenAIClient:
    async def generate_post(self, channel, prompt):
        return "Новый опубликованный пост"


class FakeTelegramClient:
    def __init__(self) -> None:
        self.photo_caption = None

    async def send_message(self, chat_id, text, options):
        return [SentMessage(chat_id=chat_id, message_id=101)]

    async def send_photo(self, chat_id, photo, filename, mime_type, caption, options):
        self.photo_caption = caption
        return SentMessage(chat_id=chat_id, message_id=202)


class FakeImageService:
    def __init__(self, image=None, error=None) -> None:
        self.image = image
        self.error = error

    async def prepare(self, channel, post_text):
        if self.error:
            raise self.error
        return self.image


@pytest.mark.asyncio
async def test_publisher_uses_enabled_history_and_records_delivered_post(tmp_path) -> None:
    channel = ChannelConfig(
        key="history_channel",
        title="History channel",
        chat_id="@history_channel",
        schedule="0 10 * * *",
        prompt_file=Path("prompts/test.md"),
        history_enabled=True,
        history_posts_limit=5,
    )
    settings = Settings(
        project_root=tmp_path,
        openai_api_key="dummy",
        telegram_bot_token="dummy",
        telegram_webhook_secret="dummy",
    )
    history_store = PostHistoryStore(tmp_path / "history.sqlite3")
    history_store.add(channel.key, "Предыдущий пост", [100], "schedule")
    renderer = FakePromptRenderer()
    publisher = Publisher(
        settings=settings,
        channels_config=ChannelsConfig(channels=[channel]),
        prompt_renderer=renderer,
        openai_client=FakeOpenAIClient(),
        telegram_client=FakeTelegramClient(),
        post_history=history_store,
        image_service=FakeImageService(),
    )

    result = await publisher.publish(channel.key, reason="manual", force=True)

    assert result.delivered is True
    assert [entry.text for entry in renderer.received_history] == ["Предыдущий пост"]
    assert [entry.text for entry in history_store.recent(channel.key, 10)] == [
        "Новый опубликованный пост",
        "Предыдущий пост",
    ]


@pytest.mark.asyncio
async def test_publisher_does_not_inject_history_when_disabled(tmp_path) -> None:
    channel = ChannelConfig(
        key="plain_channel",
        title="Plain channel",
        chat_id="@plain_channel",
        schedule="0 10 * * *",
        prompt_file=Path("prompts/test.md"),
        history_enabled=False,
    )
    settings = Settings(
        project_root=tmp_path,
        openai_api_key="dummy",
        telegram_bot_token="dummy",
        telegram_webhook_secret="dummy",
    )
    history_store = PostHistoryStore(tmp_path / "history.sqlite3")
    history_store.add(channel.key, "Предыдущий пост", [100], "schedule")
    renderer = FakePromptRenderer()
    publisher = Publisher(
        settings=settings,
        channels_config=ChannelsConfig(channels=[channel]),
        prompt_renderer=renderer,
        openai_client=FakeOpenAIClient(),
        telegram_client=FakeTelegramClient(),
        post_history=history_store,
        image_service=FakeImageService(),
    )

    await publisher.publish(channel.key, reason="manual", force=True)

    assert renderer.received_history is None
    assert len(history_store.recent(channel.key, 10)) == 2


@pytest.mark.asyncio
async def test_publisher_sends_short_post_as_photo_caption(tmp_path) -> None:
    channel = ChannelConfig(
        key="image_channel",
        title="Image channel",
        chat_id="@image_channel",
        schedule="0 10 * * *",
        prompt_file=Path("prompts/test.md"),
        image={"mode": "generate"},
    )
    settings = Settings(
        project_root=tmp_path,
        openai_api_key="dummy",
        telegram_bot_token="dummy",
        telegram_webhook_secret="dummy",
    )
    telegram_client = FakeTelegramClient()
    image = PreparedImage(
        content=b"image",
        filename="post.jpg",
        mime_type="image/jpeg",
        source="generated",
        brief="editorial image",
    )
    publisher = Publisher(
        settings=settings,
        channels_config=ChannelsConfig(channels=[channel]),
        prompt_renderer=FakePromptRenderer(),
        openai_client=FakeOpenAIClient(),
        telegram_client=telegram_client,
        post_history=PostHistoryStore(tmp_path / "history.sqlite3"),
        image_service=FakeImageService(image=image),
    )

    result = await publisher.publish(channel.key, reason="manual", force=True)

    assert result.image_delivered is True
    assert result.image_source == "generated"
    assert result.message_ids == [202]
    assert telegram_client.photo_caption == "Новый опубликованный пост"


@pytest.mark.asyncio
async def test_publisher_falls_back_to_text_when_image_fails(tmp_path) -> None:
    channel = ChannelConfig(
        key="fallback_channel",
        title="Fallback channel",
        chat_id="@fallback_channel",
        schedule="0 10 * * *",
        prompt_file=Path("prompts/test.md"),
        image={"mode": "search", "fallback_to_text": True},
    )
    settings = Settings(
        project_root=tmp_path,
        openai_api_key="dummy",
        telegram_bot_token="dummy",
        telegram_webhook_secret="dummy",
    )
    publisher = Publisher(
        settings=settings,
        channels_config=ChannelsConfig(channels=[channel]),
        prompt_renderer=FakePromptRenderer(),
        openai_client=FakeOpenAIClient(),
        telegram_client=FakeTelegramClient(),
        post_history=PostHistoryStore(tmp_path / "history.sqlite3"),
        image_service=FakeImageService(error=ImagePreparationError("Pexels unavailable")),
    )

    result = await publisher.publish(channel.key, reason="manual", force=True)

    assert result.delivered is True
    assert result.image_delivered is False
    assert result.image_error == "Pexels unavailable"
    assert result.message_ids == [101]
