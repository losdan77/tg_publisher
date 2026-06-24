from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    AsyncOpenAI,
    AuthenticationError,
    RateLimitError,
)

from app.config import ChannelConfig
from app.settings import Settings


class OpenAIGenerationError(RuntimeError):
    pass


class OpenAITextClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = AsyncOpenAI(
            api_key=settings.openai_key_value,
            timeout=settings.openai_timeout_seconds,
        )

    async def close(self) -> None:
        await self.client.close()

    async def generate_post(self, channel: ChannelConfig, prompt: str) -> str:
        request: dict[str, Any] = {
            "model": channel.model or self.settings.openai_default_model,
            "input": prompt,
            "max_output_tokens": channel.max_output_tokens,
        }

        if channel.temperature is not None:
            request["temperature"] = channel.temperature
        if channel.reasoning_effort is not None:
            request["reasoning"] = {"effort": channel.reasoning_effort}
        if channel.text_verbosity is not None:
            request["text"] = {"verbosity": channel.text_verbosity}

        return await self._generate_text(
            request,
            empty_message="OpenAI вернул пустой ответ. Попробуй ещё раз или измени prompt.",
        )

    async def generate_image_brief(self, channel: ChannelConfig, post_text: str) -> str:
        visual_direction = channel.image.prompt.strip() or (
            "Clean editorial photography, natural composition, no text, no logos, no watermarks."
        )
        if channel.image.mode == "search":
            task = (
                "Return only a concise stock-photo search query in English: 3-7 concrete keywords. "
                "Describe visible subjects and setting; do not include explanations, quotes or camera parameters."
            )
        else:
            task = (
                "Return only a detailed image-generation prompt in English, 80-160 words. "
                "Create one coherent scene that illustrates the post. Do not request visible text, logos or watermarks."
            )

        request: dict[str, Any] = {
            "model": channel.model or self.settings.openai_default_model,
            "input": (
                f"{task}\n\nChannel visual direction:\n{visual_direction}\n\n"
                f"Telegram post:\n{post_text[:6000]}"
            ),
            "max_output_tokens": 300,
        }
        return await self._generate_text(
            request,
            empty_message="OpenAI не смог сформировать описание изображения.",
        )

    async def _generate_text(self, request: dict[str, Any], empty_message: str) -> str:
        try:
            response = await self.client.responses.create(**request)
        except AuthenticationError as exc:
            raise OpenAIGenerationError(
                "OpenAI отклонил API-ключ. Проверь OPENAI_API_KEY в GitHub secret ENV_FILE: "
                "значение должно начинаться с sk- и не должно содержать повторное OPENAI_API_KEY=."
            ) from exc
        except RateLimitError as exc:
            raise OpenAIGenerationError(
                "OpenAI временно отклонил запрос из-за лимита или отсутствия доступного баланса. "
                "Проверь billing и usage в OpenAI Platform."
            ) from exc
        except APIConnectionError as exc:
            raise OpenAIGenerationError(
                "Не удалось соединиться с OpenAI. Проверь интернет на VPS и повтори публикацию."
            ) from exc
        except APIStatusError as exc:
            raise OpenAIGenerationError(
                f"OpenAI вернул ошибку HTTP {exc.status_code}. Проверь модель и параметры канала."
            ) from exc

        text = extract_response_text(response)
        if not text:
            raise OpenAIGenerationError(empty_message)
        return text


def extract_response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    data: dict[str, Any]
    if hasattr(response, "model_dump"):
        data = response.model_dump()
    elif isinstance(response, dict):
        data = response
    else:
        return ""

    chunks: list[str] = []
    for output_item in data.get("output", []):
        for content_item in output_item.get("content", []):
            if content_item.get("type") in {"output_text", "text"}:
                text = content_item.get("text")
                if isinstance(text, str):
                    chunks.append(text)
    return "\n".join(chunks).strip()
