from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from jellyfleet.jellyfin.client import JellyfinClient

from jellyfleet.jellyfin.libraries import LibrariesClient
from jellyfleet.sync.diff import compare_libraries, compute_diff


class LibrarySync:
    def __init__(
        self, father_client: JellyfinClient, child_client: JellyfinClient
    ) -> None:
        self.father_client = father_client
        self.child_client = child_client
        self.father_libraries = LibrariesClient(father_client)
        self.child_libraries = LibrariesClient(child_client)
        self.logger = logging.getLogger(__name__)

    async def sync_libraries(self, dry_run: bool = True) -> dict[str, Any]:
        self.logger.info("Starting library synchronization")

        father_libraries = await self.father_libraries.get_libraries()
        child_libraries = await self.child_libraries.get_libraries()

        diff = compute_diff(
            father_libraries,
            child_libraries,
            key_func=lambda lib: lib["Name"],
            compare_func=compare_libraries,
        )

        results = {
            "added": [],
            "removed": [],
            "modified": [],
            "errors": [],
        }

        for library in diff.added:
            try:
                if not dry_run:
                    paths = self._extract_paths_from_library(library)
                    created_lib = await self.child_libraries.create_library(
                        library["Name"],
                        library["CollectionType"],
                        paths,
                    )
                    results["added"].append(
                        {
                            "name": library["Name"],
                            "id": created_lib.get("Id"),
                            "collection_type": library["CollectionType"],
                            "paths": paths,
                            "action": "created",
                        }
                    )
                else:
                    paths = self._extract_paths_from_library(library)
                    results["added"].append(
                        {
                            "name": library["Name"],
                            "collection_type": library["CollectionType"],
                            "paths": paths,
                            "action": "would_create",
                        }
                    )
                self.logger.info("Library %s would be added", library["Name"])
            except Exception as err:
                library_name = library["Name"]
                self.logger.exception("Failed to add library %s", library_name)
                error_msg = f"Failed to add library {library_name}: {err}"
                results["errors"].append(error_msg)

        for library in diff.removed:
            try:
                if not dry_run:
                    await self.child_libraries.delete_library(library["Id"])
                    results["removed"].append(
                        {
                            "name": library["Name"],
                            "id": library["Id"],
                            "action": "deleted",
                        }
                    )
                else:
                    results["removed"].append(
                        {
                            "name": library["Name"],
                            "id": library["Id"],
                            "action": "would_delete",
                        }
                    )
                self.logger.info("Library %s would be removed", library["Name"])
            except Exception as err:
                library_name = library["Name"]
                self.logger.exception("Failed to remove library %s", library_name)
                error_msg = f"Failed to remove library {library_name}: {err}"
                results["errors"].append(error_msg)

        for father_lib, child_lib in diff.modified:
            try:
                library_updates = self._extract_library_updates(father_lib, child_lib)

                if library_updates and not dry_run:
                    await self.child_libraries.update_library(
                        child_lib["Id"], library_updates
                    )
                    results["modified"].append(
                        {
                            "name": father_lib["Name"],
                            "id": child_lib["Id"],
                            "updates": library_updates,
                            "action": "updated",
                        }
                    )
                elif library_updates:
                    results["modified"].append(
                        {
                            "name": father_lib["Name"],
                            "id": child_lib["Id"],
                            "updates": library_updates,
                            "action": "would_update",
                        }
                    )

                self.logger.info("Library %s would be modified", father_lib["Name"])
            except Exception as err:
                library_name = father_lib["Name"]
                self.logger.exception("Failed to modify library %s", library_name)
                error_msg = f"Failed to modify library {library_name}: {err}"
                results["errors"].append(error_msg)

        total_actions = (
            len(results["added"]) + len(results["removed"]) + len(results["modified"])
        )
        self.logger.info(
            "Library synchronization completed: %d total actions, %d errors",
            total_actions,
            len(results["errors"]),
        )

        return results

    def _extract_paths_from_library(self, library: dict[str, Any]) -> list[str]:
        library_options = library.get("LibraryOptions", {})
        path_infos = library_options.get("PathInfos", [])
        return [
            path_info.get("Path", "")
            for path_info in path_infos
            if path_info.get("Path")
        ]

    def _extract_library_updates(
        self, father_lib: dict[str, Any], child_lib: dict[str, Any]
    ) -> dict[str, Any]:
        updates = {}

        if father_lib.get("CollectionType") != child_lib.get("CollectionType"):
            updates["CollectionType"] = father_lib["CollectionType"]

        father_paths = self._extract_paths_from_library(father_lib)
        child_paths = self._extract_paths_from_library(child_lib)

        if set(father_paths) != set(child_paths):
            updates["LibraryOptions"] = {
                "PathInfos": [{"Path": path} for path in father_paths]
            }

        return updates
