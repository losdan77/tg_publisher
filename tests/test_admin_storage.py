from pathlib import Path

from app.admin_storage import assert_safe_prompt_path, write_prompt


def test_write_prompt_normalizes_prompt_path(tmp_path: Path) -> None:
    path = write_prompt(tmp_path, "new_channel.md", "hello")

    assert path == "prompts/new_channel.md"
    assert (tmp_path / "prompts/new_channel.md").read_text(encoding="utf-8") == "hello"


def test_prompt_path_must_stay_inside_prompts(tmp_path: Path) -> None:
    try:
        assert_safe_prompt_path(tmp_path, "../secret.md")
    except ValueError as exc:
        assert "Prompt file" in str(exc)
    else:
        raise AssertionError("path traversal should be rejected")

