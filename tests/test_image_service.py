import base64
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from app.config import ChannelConfig
from app.image_service import PostImageService
from app.settings import Settings


def make_channel(image: dict) -> ChannelConfig:
    return ChannelConfig(
        key="image_channel",
        title="Image channel",
        chat_id="@image_channel",
        schedule="0 10 * * *",
        prompt_file="prompts/test.md",
        image=image,
    )


@pytest.mark.asyncio
async def test_generate_image_returns_decoded_jpeg(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        openai_api_key="dummy",
        telegram_bot_token="dummy",
        telegram_webhook_secret="dummy",
    )
    openai_client = SimpleNamespace(
        generate_image_brief=AsyncMock(return_value="A cinematic editorial scene"),
        client=SimpleNamespace(
            images=SimpleNamespace(
                generate=AsyncMock(
                    return_value=SimpleNamespace(
                        data=[SimpleNamespace(b64_json=base64.b64encode(b"jpeg-data").decode(), url=None)]
                    )
                )
            )
        ),
    )
    service = PostImageService(settings, openai_client)

    try:
        image = await service.prepare(make_channel({"mode": "generate"}), "Текст поста")
    finally:
        await service.close()

    assert image is not None
    assert image.content == b"jpeg-data"
    assert image.source == "generated"
    openai_client.client.images.generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_image_uses_pexels_and_downloads_photo(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        openai_api_key="dummy",
        telegram_bot_token="dummy",
        telegram_webhook_secret="dummy",
        pexels_api_key="pexels-test-key",
    )
    openai_client = SimpleNamespace(
        generate_image_brief=AsyncMock(return_value="software team office"),
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "api.pexels.com":
            assert request.headers["Authorization"] == "pexels-test-key"
            return httpx.Response(
                200,
                json={
                    "photos": [
                        {
                            "photographer": "Test Photographer",
                            "url": "https://www.pexels.com/photo/123/",
                            "src": {"large2x": "https://images.pexels.com/photo.jpg"},
                        }
                    ]
                },
            )
        return httpx.Response(200, content=b"photo-data", headers={"content-type": "image/jpeg"})

    service = PostImageService(settings, openai_client)
    await service.http.aclose()
    service.http = httpx.AsyncClient(transport=httpx.MockTransport(handler))

    try:
        image = await service.prepare(make_channel({"mode": "search"}), "Текст поста")
    finally:
        await service.close()

    assert image is not None
    assert image.content == b"photo-data"
    assert image.source == "pexels"
    assert image.credit == "Фото: Test Photographer / Pexels"
