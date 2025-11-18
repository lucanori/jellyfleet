from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from jellyfleet.jellyfin.client import JellyfinClient


class LibrariesClient:
    def __init__(self, client: JellyfinClient) -> None:
        self.client = client

    async def get_libraries(self) -> list[dict[str, Any]]:
        response = await self.client.get("/Library/VirtualFolders")
        return response if isinstance(response, list) else []

    async def get_library(self, library_id: str) -> dict[str, Any]:
        return await self.client.get(f"/Library/VirtualFolders/{library_id}")

    async def create_library(
        self, name: str, collection_type: str, paths: list[str]
    ) -> dict[str, Any]:
        payload = {
            "Name": name,
            "CollectionType": collection_type,
            "LibraryOptions": {"PathInfos": [{"Path": path} for path in paths]},
        }
        return await self.client.post("/Library/VirtualFolders", json=payload)

    async def update_library(
        self, library_id: str, library_info: dict[str, Any]
    ) -> dict[str, Any]:
        return await self.client.post(
            f"/Library/VirtualFolders/{library_id}", json=library_info
        )

    async def delete_library(self, library_id: str) -> None:
        await self.client.delete(f"/Library/VirtualFolders/{library_id}")

    async def refresh_library(self, library_id: str) -> dict[str, Any]:
        return await self.client.post(f"/Library/VirtualFolders/{library_id}/Refresh")

    async def get_library_items(self, library_id: str) -> list[dict[str, Any]]:
        params = {"ParentId": library_id, "Recursive": True}
        response = await self.client.get("/Users/Items", params=params)
        return response.get("Items", []) if isinstance(response, dict) else []
