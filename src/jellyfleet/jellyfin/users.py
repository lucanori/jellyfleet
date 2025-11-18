from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from jellyfleet.jellyfin.client import JellyfinClient


class UsersClient:
    def __init__(self, client: JellyfinClient) -> None:
        self.client = client

    async def get_users(self) -> list[dict[str, Any]]:
        response = await self.client.get("/Users")
        return response if isinstance(response, list) else []

    async def get_user(self, user_id: str) -> dict[str, Any]:
        return await self.client.get(f"/Users/{user_id}")

    async def create_user(self, name: str, password: str) -> dict[str, Any]:
        payload = {"Name": name, "Password": password}
        return await self.client.post("/Users/New", json=payload)

    async def update_user(
        self, user_id: str, updates: dict[str, Any]
    ) -> dict[str, Any]:
        return await self.client.post(f"/Users/{user_id}", json=updates)

    async def delete_user(self, user_id: str) -> None:
        await self.client.delete(f"/Users/{user_id}")

    async def update_user_policy(
        self, user_id: str, policy: dict[str, Any]
    ) -> dict[str, Any]:
        return await self.client.post(f"/Users/{user_id}/Policy", json=policy)

    async def update_user_configuration(
        self, user_id: str, config: dict[str, Any]
    ) -> dict[str, Any]:
        return await self.client.post(f"/Users/{user_id}/Configuration", json=config)

    async def get_user_policy(self, user_id: str) -> dict[str, Any]:
        return await self.client.get(f"/Users/{user_id}/Policy")

    async def get_user_configuration(self, user_id: str) -> dict[str, Any]:
        return await self.client.get(f"/Users/{user_id}/Configuration")
