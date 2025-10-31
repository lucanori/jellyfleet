from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from jellyfleet.db.models import SyncRun
from jellyfleet.db.repository import SyncRepository
from jellyfleet.jellyfin.client import JellyfinClient
from jellyfleet.sync.libraries import LibrarySync
from jellyfleet.sync.settings import SettingsSync
from jellyfleet.sync.users import UserSync


class SyncOrchestrator:
    def __init__(
        self,
        father_client: JellyfinClient,
        child_client: JellyfinClient,
        repository: SyncRepository,
        combination_name: str,
        domains: list[str],
    ) -> None:
        self.father_client = father_client
        self.child_client = child_client
        self.repository = repository
        self.combination_name = combination_name
        self.domains = domains
        self.father_server = father_client.url
        self.child_server = child_client.url

        self.user_sync = UserSync(father_client, child_client)
        self.settings_sync = SettingsSync(father_client, child_client)
        self.library_sync = LibrarySync(father_client, child_client)

        self.logger = logging.getLogger(__name__)

    async def run_sync(self, dry_run: bool = True) -> SyncRun:
        self.logger.info(
            "Starting sync orchestration for %s (dry_run=%s)",
            self.combination_name,
            dry_run,
        )

        sync_run = self.repository.create_sync_run(
            combination_name=self.combination_name,
            father_server=self.father_server,
            child_server=self.child_server,
            domains=",".join(self.domains),
            dry_run=dry_run,
        )

        try:
            results = await self._perform_sync(dry_run)

            self.repository.complete_sync_run(
                sync_run.id,
                status="completed",
                details=self._format_results(results),
                actions_count=self._count_actions(results),
            )

            self.logger.info(
                "Sync orchestration completed successfully for %s",
                self.combination_name,
            )

        except Exception as err:
            error_message = f"Sync orchestration failed: {err}"
            self.logger.error(error_message)

            self.repository.complete_sync_run(
                sync_run.id,
                status="failed",
                error_message=error_message,
            )

            raise

        return self.repository.get_sync_run(sync_run.id)

    async def _perform_sync(self, dry_run: bool) -> dict[str, Any]:
        results = {
            "users": {},
            "settings": {},
            "libraries": {},
            "start_time": datetime.now(timezone.utc).isoformat(),
        }

        try:
            self.logger.info("Syncing server settings")
            results["settings"] = await self.settings_sync.sync_server_settings(dry_run)
        except Exception as err:
            self.logger.error("Failed to sync server settings: %s", err)
            results["settings"] = {"errors": [str(err)]}

        try:
            self.logger.info("Syncing users")
            results["users"] = await self.user_sync.sync_users(dry_run)
        except Exception as err:
            self.logger.error("Failed to sync users: %s", err)
            results["users"] = {"errors": [str(err)]}

        try:
            self.logger.info("Syncing libraries")
            results["libraries"] = await self.library_sync.sync_libraries(dry_run)
        except Exception as err:
            self.logger.error("Failed to sync libraries: %s", err)
            results["libraries"] = {"errors": [str(err)]}

        results["end_time"] = datetime.now(timezone.utc).isoformat()
        return results

    def _format_results(self, results: dict[str, Any]) -> str:
        formatted_parts = []

        for domain, domain_results in results.items():
            if domain in ["start_time", "end_time"]:
                continue

            if isinstance(domain_results, dict):
                total_actions = 0
                total_errors = len(domain_results.get("errors", []))

                for action_type, actions in domain_results.items():
                    if action_type == "errors":
                        continue
                    if isinstance(actions, list):
                        total_actions += len(actions)

                if total_actions > 0 or total_errors > 0:
                    formatted_parts.append(
                        f"{domain.title()}: {total_actions} actions, {total_errors} errors"
                    )

        return "; ".join(formatted_parts) if formatted_parts else "No changes needed"

    def _count_actions(self, results: dict[str, Any]) -> int:
        total_actions = 0

        for domain, domain_results in results.items():
            if domain in ["start_time", "end_time"]:
                continue

            if isinstance(domain_results, dict):
                for action_type, actions in domain_results.items():
                    if action_type == "errors":
                        continue
                    if isinstance(actions, list):
                        total_actions += len(actions)

        return total_actions
