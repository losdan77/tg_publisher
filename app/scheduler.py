import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import ChannelsConfig
from app.publisher import Publisher

logger = logging.getLogger(__name__)


class ChannelScheduler:
    def __init__(self, publisher: Publisher):
        self.publisher = publisher
        self.scheduler = AsyncIOScheduler(timezone="UTC")

    def start(self, channels_config: ChannelsConfig) -> None:
        self.reload(channels_config)
        self.scheduler.start()
        logger.info("Scheduler started with %s jobs", len(self.scheduler.get_jobs()))

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")

    def reload(self, channels_config: ChannelsConfig) -> None:
        for job in self.scheduler.get_jobs():
            self.scheduler.remove_job(job.id)

        for channel in channels_config.enabled_channels:
            trigger = CronTrigger.from_crontab(channel.schedule, timezone=channel.timezone)
            self.scheduler.add_job(
                self._publish_job,
                trigger=trigger,
                id=f"publish:{channel.key}",
                name=f"Publish {channel.key}",
                kwargs={"channel_key": channel.key},
                coalesce=True,
                max_instances=1,
                misfire_grace_time=300,
            )
            logger.info(
                "Scheduled channel=%s cron='%s' timezone=%s",
                channel.key,
                channel.schedule,
                channel.timezone,
            )

    def jobs_snapshot(self) -> list[dict[str, str | None]]:
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            }
            for job in self.scheduler.get_jobs()
        ]

    async def _publish_job(self, channel_key: str) -> None:
        try:
            await self.publisher.publish(channel_key, reason="schedule")
        except Exception:
            logger.exception("Scheduled publish failed channel=%s", channel_key)

