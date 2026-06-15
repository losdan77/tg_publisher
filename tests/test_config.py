from pathlib import Path

from app.config import load_channels_config


def test_load_channels_config() -> None:
    project_root = Path(__file__).resolve().parents[1]
    config = load_channels_config(project_root / "config/channels.yaml", project_root)

    assert len(config.channels) == 1
    assert config.channels[0].key == "test_ai_news"
    assert config.channels[0].enabled is False


def test_duplicate_channel_keys_are_rejected(tmp_path: Path) -> None:
    prompt = tmp_path / "prompt.md"
    prompt.write_text("hello", encoding="utf-8")
    config_path = tmp_path / "channels.yaml"
    config_path.write_text(
        """
channels:
  - key: one
    title: One
    chat_id: '@one'
    schedule: '0 10 * * *'
    prompt_file: prompt.md
  - key: one
    title: Duplicate
    chat_id: '@two'
    schedule: '0 11 * * *'
    prompt_file: prompt.md
""",
        encoding="utf-8",
    )

    try:
        load_channels_config(config_path, tmp_path)
    except ValueError as exc:
        assert "duplicate channel keys" in str(exc)
    else:
        raise AssertionError("duplicate keys should fail validation")

