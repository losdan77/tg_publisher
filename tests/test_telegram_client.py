import httpx
import pytest

from app.config import TelegramOptions
from app.telegram_client import TelegramBotClient, split_telegram_text


def test_split_telegram_text_keeps_short_text_as_single_chunk() -> None:
    assert split_telegram_text("hello") == ["hello"]


def test_split_telegram_text_splits_long_text() -> None:
    text = "word " * 2000
    chunks = split_telegram_text(text, limit=100)

    assert len(chunks) > 1
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_split_telegram_text_splits_long_word() -> None:
    chunks = split_telegram_text("x" * 250, limit=100)

    assert [len(chunk) for chunk in chunks] == [100, 100, 50]


@pytest.mark.asyncio
async def test_send_photo_uploads_multipart_file() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/sendPhoto")
        assert request.headers["content-type"].startswith("multipart/form-data")
        body = await request.aread()
        assert b"photo-bytes" in body
        assert "Подпись".encode() in body
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 55, "chat": {"id": -100}}})

    client = TelegramBotClient("test-token")
    await client.http.aclose()
    client.http = httpx.AsyncClient(transport=httpx.MockTransport(handler))

    try:
        result = await client.send_photo(
            chat_id=-100,
            photo=b"photo-bytes",
            filename="post.jpg",
            mime_type="image/jpeg",
            caption="Подпись",
            options=TelegramOptions(parse_mode="HTML"),
        )
    finally:
        await client.close()

    assert result.message_id == 55
