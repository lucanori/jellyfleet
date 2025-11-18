from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from jellyfleet.jellyfin.client import JellyfinClient


class SettingsClient:
    def __init__(self, client: JellyfinClient) -> None:
        self.client = client

    async def get_server_configuration(self) -> dict[str, Any]:
        return await self.client.get("/System/Configuration")

    async def update_server_configuration(
        self, config: dict[str, Any]
    ) -> dict[str, Any]:
        return await self.client.post("/System/Configuration", json=config)

    async def get_display_preferences(
        self, user_id: str, display_preferences_id: str
    ) -> dict[str, Any]:
        return await self.client.get(
            f"/Users/{user_id}/DisplayPreferences/{display_preferences_id}"
        )

    async def update_display_preferences(
        self, user_id: str, display_preferences_id: str, preferences: dict[str, Any]
    ) -> dict[str, Any]:
        return await self.client.post(
            f"/Users/{user_id}/DisplayPreferences/{display_preferences_id}",
            json=preferences,
        )

    async def get_user_item_data(self, user_id: str) -> dict[str, Any]:
        return await self.client.get(f"/Users/{user_id}/Items")
