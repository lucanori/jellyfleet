import json

import pytest
from pydantic import SecretStr

from jellyfleet.jellyfin.client import JellyfinClient
from jellyfleet.jellyfin.settings import SettingsClient


@pytest.mark.asyncio
async def test_settings_client_get_server_configuration(httpx_mock):
    test_config = {"ServerName": "Test Server", "UICulture": "en-US"}
    httpx_mock.add_response(
        method="GET", url="https://example.com/System/Configuration", json=test_config
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    settings_client = SettingsClient(base_client)

    result = await settings_client.get_server_configuration()
    assert result == test_config


@pytest.mark.asyncio
async def test_settings_client_update_server_configuration(httpx_mock):
    test_config = {"ServerName": "Updated Server"}
    httpx_mock.add_response(
        method="POST", url="https://example.com/System/Configuration", json=test_config
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    settings_client = SettingsClient(base_client)

    result = await settings_client.update_server_configuration(test_config)
    assert result == test_config

    request = httpx_mock.get_request()
    assert json.loads(request.content) == test_config


@pytest.mark.asyncio
async def test_settings_client_get_display_preferences(httpx_mock):
    test_prefs = {"CustomPrefs": {"key": "value"}}
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/Users/user1/DisplayPreferences/prefs-id",
        json=test_prefs,
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    settings_client = SettingsClient(base_client)

    result = await settings_client.get_display_preferences("user1", "prefs-id")
    assert result == test_prefs


@pytest.mark.asyncio
async def test_settings_client_update_display_preferences(httpx_mock):
    test_prefs = {"CustomPrefs": {"updated": "value"}}
    httpx_mock.add_response(
        method="POST",
        url="https://example.com/Users/user1/DisplayPreferences/prefs-id",
        json=test_prefs,
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    settings_client = SettingsClient(base_client)

    result = await settings_client.update_display_preferences(
        "user1", "prefs-id", test_prefs
    )
    assert result == test_prefs

    request = httpx_mock.get_request()
    assert json.loads(request.content) == test_prefs


@pytest.mark.asyncio
async def test_settings_client_get_user_item_data(httpx_mock):
    test_items = {"Items": [{"Id": "item1", "Name": "Item 1"}]}
    httpx_mock.add_response(
        method="GET", url="https://example.com/Users/user1/Items", json=test_items
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    settings_client = SettingsClient(base_client)

    result = await settings_client.get_user_item_data("user1")
    assert result == test_items
