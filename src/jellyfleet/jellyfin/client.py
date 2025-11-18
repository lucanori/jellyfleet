from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import httpx

from jellyfleet.jellyfin.exceptions import (
    ApiError,
    AuthenticationError,
    NetworkError,
    RateLimitError,
)

if TYPE_CHECKING:
    from pydantic import SecretStr

HTTP_STATUS_UNAUTHORIZED = 401
HTTP_STATUS_RATE_LIMIT = 429
HTTP_STATUS_CLIENT_ERROR = 400


class JellyfinClient:
    def __init__(self, url: str, token: SecretStr, timeout: int = 30) -> None:
        self.url = url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    def _get_headers(self) -> dict[str, str]:
        token_value = self.token.get_secret_value()
        return {
            "Authorization": f'MediaBrowser Token="{token_value}"',
            "Accept": "application/json",
        }

    async def _make_request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> dict[str, Any]:
        url = f"{self.url}{endpoint}"
        headers = self._get_headers()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, url, headers=headers, **kwargs)
                self.logger.debug(
                    "%s %s - Status: %s", method, endpoint, response.status_code
                )

                if response.status_code == HTTP_STATUS_UNAUTHORIZED:
                    message = "Invalid or expired token"
                    raise AuthenticationError(message)
                if response.status_code == HTTP_STATUS_RATE_LIMIT:
                    message = "Rate limit exceeded"
                    raise RateLimitError(message)
                if response.status_code >= HTTP_STATUS_CLIENT_ERROR:
                    message = f"API error: {response.text}"
                    raise ApiError(message, response.status_code)

                if response.content:
                    return response.json()
                return {}

        except httpx.TimeoutException as err:
            message = f"Request timeout after {self.timeout} seconds"
            raise NetworkError(message) from err
        except httpx.ConnectError as err:
            message = f"Failed to connect to {self.url}"
            raise NetworkError(message) from err
        except httpx.HTTPError as err:
            message = f"HTTP error: {err}"
            raise NetworkError(message) from err

    async def get(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return await self._make_request("GET", endpoint, params=params)

    async def post(
        self, endpoint: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return await self._make_request("POST", endpoint, json=json)

    async def delete(self, endpoint: str) -> dict[str, Any]:
        return await self._make_request("DELETE", endpoint)

    async def ping(self) -> bool:
        try:
            await self.get("/System/Ping")
        except (NetworkError, AuthenticationError, ApiError):
            return False
        else:
            return True
