from pathlib import Path

from app.config import load_channels_config
from app.prompting import PromptRenderer


def test_prompt_renderer_injects_channel_context() -> None:
    project_root = Path(__file__).resolve().parents[1]
    config = load_channels_config(project_root / "config/channels.yaml", project_root)
    channel = config.get_channel("test_ai_news")

    rendered = PromptRenderer(project_root).render(channel, reason="test")

    assert "Test AI News" in rendered
    assert "AI, automation, and useful tools" in rendered
    assert "{{" not in rendered

