import base64
import binascii
import hashlib
import logging
from dataclasses import dataclass
from typing import Any, Literal

import httpx
from openai import APIConnectionError, APIStatusError, AuthenticationError, RateLimitError

from app.config import ChannelConfig
from app.openai_client import OpenAIGenerationError, OpenAITextClient
from app.settings import Settings

logger = logging.getLogger(__name__)

MAX_IMAGE_BYTES = 9_500_000
PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"


class ImagePreparationError(RuntimeError):
    pass


@dataclass(frozen=True)
class PreparedImage:
    content: bytes
    filename: str
    mime_type: str
    source: Literal["generated", "pexels"]
    brief: str
    credit: str | None = None
    source_url: str | None = None


class PostImageService:
    def __init__(self, settings: Settings, openai_client: OpenAITextClient):
        self.settings = settings
        self.openai_client = openai_client
        self.http = httpx.AsyncClient(
            timeout=settings.image_timeout_seconds,
            follow_redirects=True,
        )

    async def close(self) -> None:
        await self.http.aclose()

    async def prepare(self, channel: ChannelConfig, post_text: str) -> PreparedImage | None:
        if channel.image.mode == "none":
            return None

        try:
            brief = await self.openai_client.generate_image_brief(channel, post_text)
            if channel.image.mode == "generate":
                return await self._generate(channel, brief)
            return await self._search_pexels(channel, brief, post_text)
        except ImagePreparationError:
            raise
        except OpenAIGenerationError as exc:
            raise ImagePreparationError(str(exc)) from exc
        except (AuthenticationError, RateLimitError, APIConnectionError, APIStatusError) as exc:
            raise ImagePreparationError(openai_image_error_message(exc)) from exc
        except httpx.HTTPError as exc:
            raise ImagePreparationError(f"Не удалось загрузить изображение: {exc}") from exc
        except (KeyError, TypeError, ValueError) as exc:
            raise ImagePreparationError("Сервис изображений вернул неожиданный ответ.") from exc

    async def _generate(self, channel: ChannelConfig, brief: str) -> PreparedImage:
        response = await self.openai_client.client.images.generate(
            model=channel.image.model or self.settings.openai_image_model,
            prompt=brief,
            n=1,
            size=channel.image.size,
            quality=channel.image.quality,
            output_format="jpeg",
            output_compression=85,
        )
        if not response.data:
            raise ImagePreparationError("OpenAI не вернул изображение.")

        item = response.data[0]
        encoded = getattr(item, "b64_json", None)
        if encoded:
            try:
                content = base64.b64decode(encoded, validate=True)
            except (ValueError, binascii.Error) as exc:
                raise ImagePreparationError("OpenAI вернул повреждённые данные изображения.") from exc
        else:
            image_url = getattr(item, "url", None)
            if not image_url:
                raise ImagePreparationError("OpenAI не вернул данные изображения.")
            content, _ = await self._download_image(image_url)

        validate_image_size(content)
        return PreparedImage(
            content=content,
            filename="generated-post.jpg",
            mime_type="image/jpeg",
            source="generated",
            brief=brief,
        )

    async def _search_pexels(
        self,
        channel: ChannelConfig,
        query: str,
        post_text: str,
    ) -> PreparedImage:
        api_key = self.settings.pexels_key_value
        if not api_key:
            raise ImagePreparationError(
                "Для поиска фотографий укажи PEXELS_API_KEY в ENV_FILE или выбери генерацию OpenAI."
            )

        response = await self.http.get(
            PEXELS_SEARCH_URL,
            headers={"Authorization": api_key},
            params={
                "query": query,
                "orientation": channel.image.search_orientation,
                "per_page": 15,
                "page": 1,
            },
        )
        if response.status_code >= 400:
            raise ImagePreparationError(
                f"Pexels вернул ошибку HTTP {response.status_code}. Проверь PEXELS_API_KEY."
            )

        photos = response.json().get("photos", [])
        if not photos:
            raise ImagePreparationError(f"Pexels не нашёл фотографий по запросу: {query}")

        digest = hashlib.sha256(post_text.encode("utf-8")).digest()
        photo = photos[int.from_bytes(digest[:4], "big") % len(photos)]
        source_data: dict[str, Any] = photo.get("src", {})
        image_url = source_data.get("large2x") or source_data.get("large")
        if not image_url:
            raise ImagePreparationError("Pexels вернул фотографию без ссылки для загрузки.")

        content, mime_type = await self._download_image(image_url)
        photographer = str(photo.get("photographer") or "Pexels")
        return PreparedImage(
            content=content,
            filename=image_filename(mime_type),
            mime_type=mime_type,
            source="pexels",
            brief=query,
            credit=f"Фото: {photographer} / Pexels",
            source_url=photo.get("url"),
        )

    async def _download_image(self, url: str) -> tuple[bytes, str]:
        response = await self.http.get(url)
        response.raise_for_status()
        mime_type = response.headers.get("content-type", "").split(";", maxsplit=1)[0].lower()
        if mime_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise ImagePreparationError(f"Ссылка вернула неподдерживаемый тип файла: {mime_type or 'unknown'}")
        validate_image_size(response.content)
        return response.content, mime_type


def validate_image_size(content: bytes) -> None:
    if not content:
        raise ImagePreparationError("Получен пустой файл изображения.")
    if len(content) > MAX_IMAGE_BYTES:
        raise ImagePreparationError("Изображение превышает безопасный лимит Telegram 9,5 МБ.")


def image_filename(mime_type: str) -> str:
    extension = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}.get(mime_type, "jpg")
    return f"post-image.{extension}"


def openai_image_error_message(exc: Exception) -> str:
    if isinstance(exc, AuthenticationError):
        return "OpenAI отклонил API-ключ при генерации изображения. Проверь OPENAI_API_KEY."
    if isinstance(exc, RateLimitError):
        return "OpenAI не сгенерировал изображение из-за лимита или недоступного баланса."
    if isinstance(exc, APIConnectionError):
        return "Не удалось соединиться с OpenAI для генерации изображения."
    if isinstance(exc, APIStatusError):
        return f"OpenAI вернул ошибку изображения HTTP {exc.status_code}. Проверь модель и параметры."
    return "Не удалось сгенерировать изображение."
