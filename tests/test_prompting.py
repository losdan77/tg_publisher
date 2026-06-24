from pathlib import Path

from app.config import load_channels_config
from app.post_history import PostHistoryEntry
from app.prompting import PromptRenderer


def test_prompt_renderer_injects_channel_context() -> None:
    project_root = Path(__file__).resolve().parents[1]
    config = load_channels_config(project_root / "config/channels.yaml", project_root)
    channel = config.get_channel("test_ai_news")

    rendered = PromptRenderer(project_root).render(channel, reason="test")

    assert "Test AI News" in rendered
    assert "AI, automation, and useful tools" in rendered
    assert "{{" not in rendered


def test_prompt_renderer_appends_channel_history() -> None:
    project_root = Path(__file__).resolve().parents[1]
    config = load_channels_config(project_root / "config/channels.yaml", project_root)
    channel = config.get_channel("test_ai_news")
    history = [
        PostHistoryEntry(
            channel_key=channel.key,
            published_at="2026-06-24T10:00:00+00:00",
            text="Пост про автоматизацию рабочих процессов",
            message_ids=(42,),
            reason="schedule",
        )
    ]

    rendered = PromptRenderer(project_root).render(channel, reason="test", post_history=history)

    assert "История последних публикаций этого канала" in rendered
    assert "Пост про автоматизацию рабочих процессов" in rendered
    assert "не повторяй прошлые публикации" in rendered
