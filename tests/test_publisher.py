from pathlib import Path

import pytest

from app.config import ChannelConfig, ChannelsConfig
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
    async def send_message(self, chat_id, text, options):
        return [SentMessage(chat_id=chat_id, message_id=101)]


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
    )

    await publisher.publish(channel.key, reason="manual", force=True)

    assert renderer.received_history is None
    assert len(history_store.recent(channel.key, 10)) == 2
