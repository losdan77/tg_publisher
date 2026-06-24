from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from openai import AuthenticationError

from app.config import ChannelConfig
from app.openai_client import OpenAIGenerationError, OpenAITextClient
from app.settings import Settings


@pytest.mark.asyncio
async def test_authentication_error_has_safe_friendly_message() -> None:
    settings = Settings(
        openai_api_key="sk-test",
        telegram_bot_token="123:test",
        telegram_webhook_secret="test-secret",
    )
    channel = ChannelConfig(
        key="test",
        title="Test",
        chat_id="@test",
        schedule="0 10 * * *",
        prompt_file="prompts/test.md",
    )
    client = OpenAITextClient(settings)
    response = httpx.Response(
        401,
        request=httpx.Request("POST", "https://api.openai.com/v1/responses"),
    )
    client.client.responses.create = AsyncMock(
        side_effect=AuthenticationError(
            "Incorrect API key provided: secret-value",
            response=response,
            body={"code": "invalid_api_key"},
        )
    )

    try:
        with pytest.raises(OpenAIGenerationError, match="ENV_FILE") as exc_info:
            await client.generate_post(channel, "test prompt")
    finally:
        await client.client.close()

    assert "secret-value" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_image_brief_combines_post_and_channel_visual_style() -> None:
    settings = Settings(
        openai_api_key="sk-test",
        telegram_bot_token="123:test",
        telegram_webhook_secret="test-secret",
    )
    channel = ChannelConfig(
        key="test",
        title="Test",
        chat_id="@test",
        schedule="0 10 * * *",
        prompt_file="prompts/test.md",
        image={
            "mode": "generate",
            "prompt": "Cinematic amber and blue editorial photography",
        },
    )
    client = OpenAITextClient(settings)
    client.client.responses.create = AsyncMock(
        return_value=SimpleNamespace(output_text="A detailed visual brief")
    )

    try:
        result = await client.generate_image_brief(channel, "Пост про автоматизацию бизнеса")
    finally:
        await client.close()

    request = client.client.responses.create.await_args.kwargs
    assert result == "A detailed visual brief"
    assert "Cinematic amber and blue" in request["input"]
    assert "Пост про автоматизацию бизнеса" in request["input"]
