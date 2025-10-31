import json

import pytest
from pydantic import SecretStr

from jellyfleet.jellyfin.client import JellyfinClient
from jellyfleet.jellyfin.users import UsersClient


@pytest.mark.asyncio
async def test_users_client_get_users_returns_list(httpx_mock):
    test_users = [
        {"Id": "user1", "Name": "User One"},
        {"Id": "user2", "Name": "User Two"},
    ]
    httpx_mock.add_response(
        method="GET", url="https://example.com/Users", json=test_users
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    users_client = UsersClient(base_client)

    result = await users_client.get_users()
    assert result == test_users


@pytest.mark.asyncio
async def test_users_client_get_users_handles_non_list_response(httpx_mock):
    httpx_mock.add_response(
        method="GET", url="https://example.com/Users", json={"unexpected": "response"}
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    users_client = UsersClient(base_client)

    result = await users_client.get_users()
    assert result == []


@pytest.mark.asyncio
async def test_users_client_get_user_returns_user_data(httpx_mock):
    test_user = {"Id": "user1", "Name": "User One"}
    httpx_mock.add_response(
        method="GET", url="https://example.com/Users/user1", json=test_user
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    users_client = UsersClient(base_client)

    result = await users_client.get_user("user1")
    assert result == test_user


@pytest.mark.asyncio
async def test_users_client_create_user_sends_correct_payload(httpx_mock):
    test_user = {"Id": "new-user", "Name": "New User"}
    httpx_mock.add_response(
        method="POST", url="https://example.com/Users/New", json=test_user
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    users_client = UsersClient(base_client)

    result = await users_client.create_user("New User", "password123")
    assert result == test_user

    request = httpx_mock.get_request()
    assert json.loads(request.content) == {
        "Name": "New User",
        "Password": "password123",
    }


@pytest.mark.asyncio
async def test_users_client_update_user_sends_updates(httpx_mock):
    test_user = {"Id": "user1", "Name": "Updated User"}
    httpx_mock.add_response(
        method="POST", url="https://example.com/Users/user1", json=test_user
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    users_client = UsersClient(base_client)

    updates = {"Name": "Updated User"}
    result = await users_client.update_user("user1", updates)
    assert result == test_user

    request = httpx_mock.get_request()
    assert json.loads(request.content) == updates


@pytest.mark.asyncio
async def test_users_client_delete_user_sends_delete_request(httpx_mock):
    httpx_mock.add_response(
        method="DELETE", url="https://example.com/Users/user1", json={"success": True}
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    users_client = UsersClient(base_client)

    await users_client.delete_user("user1")

    request = httpx_mock.get_request()
    assert request.method == "DELETE"
    assert request.url == "https://example.com/Users/user1"


@pytest.mark.asyncio
async def test_users_client_update_user_policy_sends_policy(httpx_mock):
    test_policy = {"IsAdministrator": False}
    httpx_mock.add_response(
        method="POST", url="https://example.com/Users/user1/Policy", json=test_policy
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    users_client = UsersClient(base_client)

    result = await users_client.update_user_policy("user1", test_policy)
    assert result == test_policy

    request = httpx_mock.get_request()
    assert json.loads(request.content) == test_policy


@pytest.mark.asyncio
async def test_users_client_update_user_configuration_sends_config(httpx_mock):
    test_config = {"PlayDefaultAudioTrack": True}
    httpx_mock.add_response(
        method="POST",
        url="https://example.com/Users/user1/Configuration",
        json=test_config,
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    users_client = UsersClient(base_client)

    result = await users_client.update_user_configuration("user1", test_config)
    assert result == test_config

    request = httpx_mock.get_request()
    assert json.loads(request.content) == test_config


@pytest.mark.asyncio
async def test_users_client_get_user_policy_returns_policy(httpx_mock):
    test_policy = {"IsAdministrator": False, "EnableContentDeletion": False}
    httpx_mock.add_response(
        method="GET", url="https://example.com/Users/user1/Policy", json=test_policy
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    users_client = UsersClient(base_client)

    result = await users_client.get_user_policy("user1")
    assert result == test_policy


@pytest.mark.asyncio
async def test_users_client_get_user_configuration_returns_config(httpx_mock):
    test_config = {"PlayDefaultAudioTrack": True, "RememberAudioSelections": True}
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/Users/user1/Configuration",
        json=test_config,
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    users_client = UsersClient(base_client)

    result = await users_client.get_user_configuration("user1")
    assert result == test_config
