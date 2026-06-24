from dataclasses import dataclass
from typing import Any

import httpx

from app.config import TelegramOptions


class TelegramApiError(RuntimeError):
    pass


@dataclass(frozen=True)
class SentMessage:
    chat_id: str | int
    message_id: int


class TelegramBotClient:
    def __init__(self, bot_token: str, timeout: float = 30.0):
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.http = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self.http.aclose()

    async def send_message(
        self,
        chat_id: str | int,
        text: str,
        options: TelegramOptions | None = None,
    ) -> list[SentMessage]:
        options = options or TelegramOptions(parse_mode=None)
        sent: list[SentMessage] = []

        for chunk in split_telegram_text(text):
            payload: dict[str, Any] = {
                "chat_id": chat_id,
                "text": chunk,
                "disable_web_page_preview": options.disable_web_page_preview,
                "protect_content": options.protect_content,
            }
            if options.parse_mode:
                payload["parse_mode"] = options.parse_mode

            data = await self._post("sendMessage", payload)
            result = data.get("result", {})
            sent.append(
                SentMessage(
                    chat_id=result.get("chat", {}).get("id", chat_id),
                    message_id=int(result["message_id"]),
                )
            )

        return sent

    async def send_photo(
        self,
        chat_id: str | int,
        photo: bytes,
        filename: str,
        mime_type: str,
        caption: str | None = None,
        options: TelegramOptions | None = None,
    ) -> SentMessage:
        options = options or TelegramOptions(parse_mode=None)
        payload: dict[str, Any] = {
            "chat_id": str(chat_id),
            "protect_content": str(options.protect_content).lower(),
        }
        if caption:
            payload["caption"] = caption
        if options.parse_mode:
            payload["parse_mode"] = options.parse_mode

        response = await self.http.post(
            f"{self.base_url}/sendPhoto",
            data=payload,
            files={"photo": (filename, photo, mime_type)},
        )
        data = parse_telegram_response(response, "sendPhoto")
        result = data.get("result", {})
        return SentMessage(
            chat_id=result.get("chat", {}).get("id", chat_id),
            message_id=int(result["message_id"]),
        )

    async def set_webhook(self, url: str, secret_token: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "url": url,
            "drop_pending_updates": True,
            "allowed_updates": ["message", "channel_post", "edited_message"],
        }
        if secret_token:
            payload["secret_token"] = secret_token
        return await self._post("setWebhook", payload)

    async def _post(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self.http.post(f"{self.base_url}/{method}", json=payload)
        return parse_telegram_response(response, method)


def parse_telegram_response(response: httpx.Response, method: str) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError as exc:
        raise TelegramApiError(f"Telegram returned non-JSON response: {response.text}") from exc

    if response.status_code >= 400 or not data.get("ok"):
        description = data.get("description", response.text)
        raise TelegramApiError(f"Telegram {method} failed: {description}")
    return data


def split_telegram_text(text: str, limit: int = 3900) -> list[str]:
    text = text.strip()
    if not text:
        return [""]
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph.strip()
        if len(candidate) <= limit:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(paragraph) <= limit:
            current = paragraph.strip()
        else:
            chunks.extend(_split_long_piece(paragraph, limit))

    if current:
        chunks.append(current)
    return chunks


def _split_long_piece(piece: str, limit: int) -> list[str]:
    words = piece.split()
    chunks: list[str] = []
    current = ""
    for word in words:
        if len(word) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(word[index : index + limit] for index in range(0, len(word), limit))
            continue

        candidate = f"{current} {word}".strip()
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = word
    if current:
        chunks.append(current)
    return chunks
