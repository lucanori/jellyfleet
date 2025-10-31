import asyncio
import logging
from contextlib import suppress
from datetime import datetime, timezone

from croniter import croniter

from jellyfleet.config.loader import load_config
from jellyfleet.db.base import create_database_engine, create_session_factory
from jellyfleet.db.repository import SyncRepository
from jellyfleet.jellyfin.client import JellyfinClient
from jellyfleet.sync.orchestrator import SyncOrchestrator


class Scheduler:
    def __init__(self, config_path: str, interval: str = "6h") -> None:
        self.config_path = config_path
        self.interval = interval
        self.logger = logging.getLogger(__name__)
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the scheduler"""
        if self._running:
            self.logger.warning("Scheduler is already running")
            return

        self._running = True
        self.logger.info("Starting scheduler with interval: %s", self.interval)

        self._task = asyncio.create_task(self._run_scheduler())

    async def stop(self) -> None:
        """Stop the scheduler"""
        if not self._running:
            return

        self._running = False
        self.logger.info("Stopping scheduler")

        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    async def _run_scheduler(self) -> None:
        """Main scheduler loop"""
        cron = croniter(self.interval, datetime.now(timezone.utc))

        while self._running:
            next_run = cron.get_next(datetime)
            now = datetime.now(timezone.utc)

            if next_run <= now:
                await self._run_scheduled_sync()
                cron = croniter(self.interval, datetime.now(timezone.utc))
                next_run = cron.get_next(datetime)

            sleep_seconds = (next_run - now).total_seconds()
            if sleep_seconds > 0:
                self.logger.debug("Next sync in %.0f seconds", sleep_seconds)
                await asyncio.sleep(min(sleep_seconds, 60))

    async def _run_scheduled_sync(self) -> None:
        """Run a scheduled sync"""
        self.logger.info("Running scheduled sync")

        try:
            config = await load_config(self.config_path)

            engine = create_database_engine("jellyfleet.db")
            session_factory = create_session_factory(engine)

            try:
                with session_factory() as session:
                    repository = SyncRepository(session)

                    for combo in config.combinations:
                        father_server = config.servers[combo.father]

                        for child_config in combo.children:
                            child_server = config.servers[child_config.server]

                            try:
                                father_client = JellyfinClient(
                                    url=str(father_server.url),
                                    token=father_server.token,
                                )

                                child_client = JellyfinClient(
                                    url=str(child_server.url),
                                    token=child_server.token,
                                )

                                orchestrator = SyncOrchestrator(
                                    father_client=father_client,
                                    child_client=child_client,
                                    repository=repository,
                                    combination_name=f"{combo.name}-{child_config.server}",
                                    domains=[
                                        domain.value for domain in child_config.domains
                                    ],
                                )

                                sync_run = await orchestrator.run_sync(dry_run=False)

                                combination_name = f"{combo.name}-{child_config.server}"
                                self.logger.info(
                                    "Scheduled sync completed for %s: %s (%d actions)",
                                    combination_name,
                                    sync_run.status,
                                    sync_run.actions_count,
                                )

                            except Exception:
                                combination_name = f"{combo.name}-{child_config.server}"
                                self.logger.exception(
                                    "Scheduled sync failed for %s",
                                    combination_name,
                                )
            finally:
                engine.dispose()

        except Exception:
            self.logger.exception("Scheduled sync failed")

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self._running
