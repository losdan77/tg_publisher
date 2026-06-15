from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from jinja2 import Environment, StrictUndefined

from app.config import ChannelConfig, resolve_prompt_path


class PromptRenderer:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.environment = Environment(
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=StrictUndefined,
        )

    def render(self, channel: ChannelConfig, reason: str) -> str:
        prompt_path = resolve_prompt_path(self.project_root, channel.prompt_file)
        template_source = prompt_path.read_text(encoding="utf-8")
        template = self.environment.from_string(template_source)
        now = datetime.now(ZoneInfo(channel.timezone))

        return template.render(
            channel=channel.model_dump(mode="json"),
            context=channel.context,
            now=now.isoformat(),
            today=now.strftime("%Y-%m-%d"),
            date_ru=now.strftime("%d.%m.%Y"),
            time=now.strftime("%H:%M"),
            reason=reason,
        ).strip()

