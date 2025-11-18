import httpx
import pytest
from pydantic import SecretStr

from jellyfleet.jellyfin.client import JellyfinClient
from jellyfleet.jellyfin.exceptions import (
    ApiError,
    AuthenticationError,
    NetworkError,
    RateLimitError,
)

HTTP_STATUS_BAD_REQUEST = 400


@pytest.mark.asyncio
async def test_client_get_headers_includes_authorization():
    client = JellyfinClient("https://example.com", SecretStr("secret-token"))
    headers = client._get_headers()
    assert headers["Authorization"] == 'MediaBrowser Token="secret-token"'
    assert headers["Accept"] == "application/json"


@pytest.mark.asyncio
async def test_client_ping_returns_true_on_success(httpx_mock):
    httpx_mock.add_response(method="GET", url="https://example.com/System/Ping")
    client = JellyfinClient("https://example.com", SecretStr("token"))
    result = await client.ping()
    assert result is True


@pytest.mark.asyncio
async def test_client_ping_returns_false_on_authentication_error(httpx_mock):
    httpx_mock.add_response(
        method="GET", url="https://example.com/System/Ping", status_code=401
    )
    client = JellyfinClient("https://example.com", SecretStr("invalid-token"))
    result = await client.ping()
    assert result is False


@pytest.mark.asyncio
async def test_client_ping_returns_false_on_network_error(httpx_mock):
    httpx_mock.add_exception(
        httpx.HTTPError("Connection failed"),
        method="GET",
        url="https://example.com/System/Ping",
    )
    client = JellyfinClient("https://example.com", SecretStr("token"))
    result = await client.ping()
    assert result is False


@pytest.mark.asyncio
async def test_client_raises_authentication_error_on_401(httpx_mock):
    httpx_mock.add_response(
        method="GET", url="https://example.com/test", status_code=401
    )
    client = JellyfinClient("https://example.com", SecretStr("invalid-token"))
    with pytest.raises(AuthenticationError):
        await client.get("/test")


@pytest.mark.asyncio
async def test_client_raises_rate_limit_error_on_429(httpx_mock):
    httpx_mock.add_response(
        method="GET", url="https://example.com/test", status_code=429
    )
    client = JellyfinClient("https://example.com", SecretStr("token"))
    with pytest.raises(RateLimitError):
        await client.get("/test")


@pytest.mark.asyncio
async def test_client_raises_api_error_on_400(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/test",
        status_code=400,
        text="Bad request",
    )
    client = JellyfinClient("https://example.com", SecretStr("token"))
    with pytest.raises(ApiError) as exc_info:
        await client.get("/test")
    assert exc_info.value.status_code == HTTP_STATUS_BAD_REQUEST


@pytest.mark.asyncio
async def test_client_ping_returns_false_on_connect_error(httpx_mock):
    httpx_mock.add_exception(
        httpx.ConnectError("Connection failed"),
        method="GET",
        url="https://example.com/System/Ping",
    )
    client = JellyfinClient("https://example.com", SecretStr("token"))
    result = await client.ping()
    assert result is False


@pytest.mark.asyncio
async def test_client_raises_network_error_on_timeout(httpx_mock):
    httpx_mock.add_exception(
        httpx.TimeoutException("Timeout"), method="GET", url="https://example.com/test"
    )
    client = JellyfinClient("https://example.com", SecretStr("token"))
    with pytest.raises(NetworkError):
        await client.get("/test")


@pytest.mark.asyncio
async def test_client_get_returns_json_response(httpx_mock):
    test_data = {"key": "value"}
    httpx_mock.add_response(
        method="GET", url="https://example.com/test", json=test_data
    )
    client = JellyfinClient("https://example.com", SecretStr("token"))
    result = await client.get("/test")
    assert result == test_data


@pytest.mark.asyncio
async def test_client_post_sends_json_data(httpx_mock):
    test_data = {"key": "value"}
    httpx_mock.add_response(
        method="POST", url="https://example.com/test", json=test_data
    )
    client = JellyfinClient("https://example.com", SecretStr("token"))
    result = await client.post("/test", json=test_data)
    assert result == test_data


@pytest.mark.asyncio
async def test_client_delete_sends_delete_request(httpx_mock):
    httpx_mock.add_response(
        method="DELETE", url="https://example.com/test", json={"success": True}
    )
    client = JellyfinClient("https://example.com", SecretStr("token"))
    result = await client.delete("/test")
    assert result == {"success": True}


@pytest.mark.asyncio
async def test_client_handles_empty_response(httpx_mock):
    httpx_mock.add_response(method="GET", url="https://example.com/test", content=b"")
    client = JellyfinClient("https://example.com", SecretStr("token"))
    result = await client.get("/test")
    assert result == {}


@pytest.mark.asyncio
async def test_url_trailing_slash_removed():
    client = JellyfinClient("https://example.com/", "token")
    assert client.url == "https://example.com"
