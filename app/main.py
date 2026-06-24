import asyncio
import hmac
import logging
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from app.admin_storage import (
    AdminStorageError,
    delete_channel,
    list_prompt_files,
    read_prompt,
    storage_status,
    upsert_channel,
    write_prompt,
)
from app.admin_ui import ADMIN_HTML
from app.config import ChannelsConfig, load_channels_config
from app.config import ChannelConfig
from app.logging_config import configure_logging
from app.openai_client import OpenAIGenerationError, OpenAITextClient
from app.post_history import PostHistoryError, PostHistoryStore
from app.prompting import PromptRenderer
from app.publisher import Publisher
from app.scheduler import ChannelScheduler
from app.settings import Settings, get_settings
from app.telegram_client import TelegramApiError, TelegramBotClient

logger = logging.getLogger(__name__)


class PublishResponse(BaseModel):
    ok: bool
    result: dict[str, Any]


class AdminSaveChannelRequest(BaseModel):
    original_key: str | None = None
    channel: ChannelConfig
    prompt_content: str | None = None


class AdminSavePromptRequest(BaseModel):
    path: str
    content: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)

    channels_config = load_channels_config(
        path=settings.resolved_channels_config_path,
        project_root=settings.project_root,
    )
    telegram_client = TelegramBotClient(settings.telegram_token_value)
    post_history = PostHistoryStore(settings.resolved_history_db_path)
    publisher = Publisher(
        settings=settings,
        channels_config=channels_config,
        prompt_renderer=PromptRenderer(settings.project_root),
        openai_client=OpenAITextClient(settings),
        telegram_client=telegram_client,
        post_history=post_history,
    )
    scheduler = ChannelScheduler(publisher)

    app.state.settings = settings
    app.state.channels_config = channels_config
    app.state.publisher = publisher
    app.state.scheduler = scheduler
    app.state.telegram_client = telegram_client
    app.state.post_history = post_history

    if settings.enable_scheduler:
        scheduler.start(channels_config)
    else:
        logger.warning("Scheduler disabled by ENABLE_SCHEDULER=false")

    try:
        yield
    finally:
        scheduler.shutdown()
        await telegram_client.close()


app = FastAPI(
    title="TG Publisher",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan,
)


async def require_admin_token(
    request: Request,
    x_admin_token: Annotated[str | None, Header()] = None,
) -> None:
    settings: Settings = request.app.state.settings
    expected = settings.admin_api_token_value
    if not expected:
        raise HTTPException(status_code=503, detail="ADMIN_API_TOKEN is not configured")
    if not hmac.compare_digest(x_admin_token or "", expected):
        raise HTTPException(status_code=403, detail="Bad admin token")


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/admin")


@app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
async def admin_page() -> HTMLResponse:
    return HTMLResponse(ADMIN_HTML)


@app.get("/api/admin/state")
async def admin_state(request: Request, _: None = Depends(require_admin_token)) -> dict[str, Any]:
    return build_admin_state(request)


@app.get("/api/admin/prompts")
async def admin_prompt(
    path: str,
    request: Request,
    _: None = Depends(require_admin_token),
) -> dict[str, str]:
    settings: Settings = request.app.state.settings
    try:
        return {"path": path, "content": read_prompt(settings.project_root, path)}
    except AdminStorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/admin/prompts")
async def save_admin_prompt(
    payload: AdminSavePromptRequest,
    request: Request,
    _: None = Depends(require_admin_token),
) -> dict[str, str]:
    settings: Settings = request.app.state.settings
    try:
        path = write_prompt(settings.project_root, payload.path, payload.content)
    except AdminStorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": "true", "path": path}


@app.post("/api/admin/channels")
async def save_admin_channel(
    payload: AdminSaveChannelRequest,
    request: Request,
    _: None = Depends(require_admin_token),
) -> dict[str, Any]:
    settings: Settings = request.app.state.settings
    try:
        if payload.prompt_content is not None:
            write_prompt(settings.project_root, str(payload.channel.prompt_file), payload.prompt_content)

        channels_config = upsert_channel(settings, payload.channel, payload.original_key)
        if payload.original_key and payload.original_key != payload.channel.key:
            request.app.state.post_history.rename_channel(payload.original_key, payload.channel.key)
    except (AdminStorageError, PostHistoryError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    apply_reloaded_config(request, channels_config)
    state = build_admin_state(request)
    state["selected_key"] = payload.channel.key
    return state


@app.delete("/api/admin/channels/{channel_key}")
async def delete_admin_channel(
    channel_key: str,
    request: Request,
    _: None = Depends(require_admin_token),
) -> dict[str, Any]:
    settings: Settings = request.app.state.settings
    try:
        channels_config = delete_channel(settings, channel_key)
    except AdminStorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    apply_reloaded_config(request, channels_config)
    return build_admin_state(request)


@app.get("/health")
async def health(request: Request) -> dict[str, Any]:
    channels_config: ChannelsConfig = request.app.state.channels_config
    scheduler: ChannelScheduler = request.app.state.scheduler
    return {
        "status": "ok",
        "channels": len(channels_config.channels),
        "enabled_channels": len(channels_config.enabled_channels),
        "scheduler_running": scheduler.scheduler.running,
        "jobs": scheduler.jobs_snapshot(),
        "storage": storage_status(request.app.state.settings),
    }


@app.get("/channels")
async def channels(request: Request, _: None = Depends(require_admin_token)) -> dict[str, Any]:
    publisher: Publisher = request.app.state.publisher
    return {"channels": publisher.list_channels()}


@app.post("/publish/{channel_key}", response_model=PublishResponse)
async def publish_channel(
    channel_key: str,
    request: Request,
    _: None = Depends(require_admin_token),
    force: bool = Query(default=False),
) -> PublishResponse:
    publisher: Publisher = request.app.state.publisher
    try:
        result = await publisher.publish(channel_key, reason="manual", force=force)
    except OpenAIGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except TelegramApiError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Telegram не принял публикацию. Проверь TELEGRAM_BOT_TOKEN, chat_id и права бота. {exc}",
        ) from exc
    return PublishResponse(ok=True, result=result.model_dump())


@app.post("/admin/reload")
async def reload_config(request: Request, _: None = Depends(require_admin_token)) -> dict[str, Any]:
    settings: Settings = request.app.state.settings
    channels_config = load_channels_config(
        path=settings.resolved_channels_config_path,
        project_root=settings.project_root,
    )
    apply_reloaded_config(request, channels_config)
    return {
        "ok": True,
        "channels": len(channels_config.channels),
        "enabled_channels": len(channels_config.enabled_channels),
        "jobs": request.app.state.scheduler.jobs_snapshot(),
    }


@app.post("/telegram/webhook/{secret}")
async def telegram_webhook(
    secret: str,
    request: Request,
    x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None,
) -> dict[str, bool]:
    settings: Settings = request.app.state.settings
    if not hmac.compare_digest(secret, settings.telegram_webhook_secret):
        raise HTTPException(status_code=404, detail="Not found")

    expected_secret_token = settings.telegram_secret_token_value
    if expected_secret_token and not hmac.compare_digest(
        x_telegram_bot_api_secret_token or "",
        expected_secret_token,
    ):
        raise HTTPException(status_code=403, detail="Bad Telegram secret token")

    update = await request.json()
    await handle_telegram_command(request, update)
    return {"ok": True}


async def handle_telegram_command(request: Request, update: dict[str, Any]) -> None:
    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    text = (message.get("text") or "").strip()
    if not text.startswith("/"):
        return

    settings: Settings = request.app.state.settings
    sender_id = message.get("from", {}).get("id")
    chat_id = message.get("chat", {}).get("id")
    if not sender_id or not chat_id:
        return

    admin_user_ids = settings.admin_telegram_user_id_set
    if not admin_user_ids:
        logger.warning("Ignoring Telegram command because ADMIN_TELEGRAM_USER_IDS is empty")
        return

    if int(sender_id) not in admin_user_ids:
        logger.warning("Ignoring Telegram command from non-admin user_id=%s", sender_id)
        return

    command, *args = text.split()
    command = command.split("@", maxsplit=1)[0].lower()

    if command == "/publish" and args:
        channel_key = args[0]
        telegram_client: TelegramBotClient = request.app.state.telegram_client
        await telegram_client.send_message(chat_id, f"Publishing {channel_key}...", None)
        asyncio.create_task(_publish_and_reply(request, chat_id, channel_key))
    elif command == "/channels":
        publisher: Publisher = request.app.state.publisher
        lines = [
            f"{item['key']}: {'on' if item['enabled'] else 'off'} | {item['schedule']}"
            for item in publisher.list_channels()
        ]
        await request.app.state.telegram_client.send_message(chat_id, "\n".join(lines) or "No channels.", None)
    elif command == "/reload":
        await _reload_from_telegram(request, chat_id)


async def _publish_and_reply(request: Request, chat_id: int, channel_key: str) -> None:
    telegram_client: TelegramBotClient = request.app.state.telegram_client
    try:
        result = await request.app.state.publisher.publish(channel_key, reason="telegram-command", force=True)
        await telegram_client.send_message(
            chat_id,
            f"Published {result.channel_key}. Telegram messages: {result.message_ids or 'dry-run'}",
            None,
        )
    except Exception as exc:
        logger.exception("Telegram command publish failed")
        await telegram_client.send_message(chat_id, f"Publish failed: {exc}", None)


async def _reload_from_telegram(request: Request, chat_id: int) -> None:
    try:
        settings: Settings = request.app.state.settings
        channels_config = load_channels_config(settings.resolved_channels_config_path, settings.project_root)
        request.app.state.channels_config = channels_config
        request.app.state.publisher.reload_config(channels_config)
        request.app.state.scheduler.reload(channels_config)
        await request.app.state.telegram_client.send_message(
            chat_id,
            f"Reloaded: {len(channels_config.channels)} channels, {len(channels_config.enabled_channels)} enabled.",
            None,
        )
    except Exception as exc:
        logger.exception("Telegram command reload failed")
        await request.app.state.telegram_client.send_message(chat_id, f"Reload failed: {exc}", None)


def apply_reloaded_config(request: Request, channels_config: ChannelsConfig) -> None:
    request.app.state.channels_config = channels_config
    request.app.state.publisher.reload_config(channels_config)
    request.app.state.scheduler.reload(channels_config)


def build_admin_state(request: Request) -> dict[str, Any]:
    settings: Settings = request.app.state.settings
    channels_config: ChannelsConfig = request.app.state.channels_config
    scheduler: ChannelScheduler = request.app.state.scheduler
    return {
        "channels": [channel.model_dump(mode="json") for channel in channels_config.channels],
        "enabled_channels": len(channels_config.enabled_channels),
        "jobs": scheduler.jobs_snapshot(),
        "prompts": list_prompt_files(settings.project_root),
        "config_path": str(settings.resolved_channels_config_path),
        "public_base_url": settings.public_base_url,
        "dry_run": settings.dry_run,
        "storage": storage_status(settings),
    }
