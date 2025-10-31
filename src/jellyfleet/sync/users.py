from __future__ import annotations

import logging
from typing import Any

from jellyfleet.jellyfin.client import JellyfinClient
from jellyfleet.jellyfin.users import UsersClient
from jellyfleet.sync.diff import (
    compare_user_configs,
    compare_user_policies,
    compare_users,
    compute_diff,
)


class UserSync:
    def __init__(
        self, father_client: JellyfinClient, child_client: JellyfinClient
    ) -> None:
        self.father_client = father_client
        self.child_client = child_client
        self.father_users = UsersClient(father_client)
        self.child_users = UsersClient(child_client)
        self.logger = logging.getLogger(__name__)

    async def sync_users(self, dry_run: bool = True) -> dict[str, Any]:
        self.logger.info("Starting user synchronization")

        father_users = await self.father_users.get_users()
        child_users = await self.child_users.get_users()

        diff = compute_diff(
            father_users,
            child_users,
            key_func=lambda user: user["Name"],
            compare_func=compare_users,
        )

        results = {
            "added": [],
            "removed": [],
            "modified": [],
            "errors": [],
        }

        for user in diff.added:
            try:
                if not dry_run:
                    created_user = await self.child_users.create_user(
                        user["Name"], "temp_password_123"
                    )
                    results["added"].append(
                        {
                            "name": user["Name"],
                            "id": created_user.get("Id"),
                            "action": "created",
                        }
                    )
                else:
                    results["added"].append(
                        {
                            "name": user["Name"],
                            "action": "would_create",
                        }
                    )
                self.logger.info("User %s would be added", user["Name"])
            except Exception as err:
                error_msg = f"Failed to add user {user['Name']}: {err}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)

        for user in diff.removed:
            try:
                if not dry_run:
                    await self.child_users.delete_user(user["Id"])
                    results["removed"].append(
                        {
                            "name": user["Name"],
                            "id": user["Id"],
                            "action": "deleted",
                        }
                    )
                else:
                    results["removed"].append(
                        {
                            "name": user["Name"],
                            "id": user["Id"],
                            "action": "would_delete",
                        }
                    )
                self.logger.info("User %s would be removed", user["Name"])
            except Exception as err:
                error_msg = f"Failed to remove user {user['Name']}: {err}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)

        for father_user, child_user in diff.modified:
            try:
                user_updates = {}

                if father_user.get("Name") != child_user.get("Name"):
                    user_updates["Name"] = father_user["Name"]

                if father_user.get("HasPassword") != child_user.get("HasPassword"):
                    user_updates["HasPassword"] = father_user["HasPassword"]

                if father_user.get("EnableAutoLogin") != child_user.get(
                    "EnableAutoLogin"
                ):
                    user_updates["EnableAutoLogin"] = father_user["EnableAutoLogin"]

                if user_updates and not dry_run:
                    await self.child_users.update_user(child_user["Id"], user_updates)
                    results["modified"].append(
                        {
                            "name": father_user["Name"],
                            "id": child_user["Id"],
                            "updates": user_updates,
                            "action": "updated",
                        }
                    )
                elif user_updates:
                    results["modified"].append(
                        {
                            "name": father_user["Name"],
                            "id": child_user["Id"],
                            "updates": user_updates,
                            "action": "would_update",
                        }
                    )

                await self._sync_user_policies(
                    father_user, child_user, dry_run, results
                )
                await self._sync_user_configurations(
                    father_user, child_user, dry_run, results
                )

                self.logger.info("User %s would be modified", father_user["Name"])
            except Exception as err:
                error_msg = f"Failed to modify user {father_user['Name']}: {err}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)

        total_actions = (
            len(results["added"]) + len(results["removed"]) + len(results["modified"])
        )
        self.logger.info(
            "User synchronization completed: %d total actions, %d errors",
            total_actions,
            len(results["errors"]),
        )

        return results

    async def _sync_user_policies(
        self,
        father_user: dict[str, Any],
        child_user: dict[str, Any],
        dry_run: bool,
        results: dict[str, Any],
    ) -> None:
        try:
            father_policy = await self.father_users.get_user_policy(father_user["Id"])
            child_policy = await self.child_users.get_user_policy(child_user["Id"])

            if not compare_user_policies(father_policy, child_policy):
                if not dry_run:
                    await self.child_users.update_user_policy(
                        child_user["Id"], father_policy
                    )
                    results["modified"].append(
                        {
                            "name": father_user["Name"],
                            "id": child_user["Id"],
                            "type": "policy",
                            "action": "updated",
                        }
                    )
                else:
                    results["modified"].append(
                        {
                            "name": father_user["Name"],
                            "id": child_user["Id"],
                            "type": "policy",
                            "action": "would_update",
                        }
                    )
        except Exception as err:
            error_msg = f"Failed to sync policy for user {father_user['Name']}: {err}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)

    async def _sync_user_configurations(
        self,
        father_user: dict[str, Any],
        child_user: dict[str, Any],
        dry_run: bool,
        results: dict[str, Any],
    ) -> None:
        try:
            father_config = await self.father_users.get_user_configuration(
                father_user["Id"]
            )
            child_config = await self.child_users.get_user_configuration(
                child_user["Id"]
            )

            if not compare_user_configs(father_config, child_config):
                if not dry_run:
                    await self.child_users.update_user_configuration(
                        child_user["Id"], father_config
                    )
                    results["modified"].append(
                        {
                            "name": father_user["Name"],
                            "id": child_user["Id"],
                            "type": "configuration",
                            "action": "updated",
                        }
                    )
                else:
                    results["modified"].append(
                        {
                            "name": father_user["Name"],
                            "id": child_user["Id"],
                            "type": "configuration",
                            "action": "would_update",
                        }
                    )
        except Exception as err:
            error_msg = (
                f"Failed to sync configuration for user {father_user['Name']}: {err}"
            )
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
