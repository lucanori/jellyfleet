import json

import pytest
from pydantic import SecretStr

from jellyfleet.jellyfin.client import JellyfinClient
from jellyfleet.jellyfin.libraries import LibrariesClient


@pytest.mark.asyncio
async def test_libraries_client_get_libraries_returns_list(httpx_mock):
    test_libraries = [
        {"Name": "Movies", "Id": "lib1", "CollectionType": "movies"},
        {"Name": "TV Shows", "Id": "lib2", "CollectionType": "tvshows"},
    ]
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/Library/VirtualFolders",
        json=test_libraries,
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    libraries_client = LibrariesClient(base_client)

    result = await libraries_client.get_libraries()
    assert result == test_libraries


@pytest.mark.asyncio
async def test_libraries_client_get_libraries_handles_non_list_response(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/Library/VirtualFolders",
        json={"unexpected": "response"},
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    libraries_client = LibrariesClient(base_client)

    result = await libraries_client.get_libraries()
    assert result == []


@pytest.mark.asyncio
async def test_libraries_client_get_library_returns_library_data(httpx_mock):
    test_library = {"Name": "Movies", "Id": "lib1", "CollectionType": "movies"}
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/Library/VirtualFolders/lib1",
        json=test_library,
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    libraries_client = LibrariesClient(base_client)

    result = await libraries_client.get_library("lib1")
    assert result == test_library


@pytest.mark.asyncio
async def test_libraries_client_create_library_sends_correct_payload(httpx_mock):
    test_library = {"Name": "New Library", "Id": "lib3"}
    httpx_mock.add_response(
        method="POST",
        url="https://example.com/Library/VirtualFolders",
        json=test_library,
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    libraries_client = LibrariesClient(base_client)

    result = await libraries_client.create_library(
        "New Library", "movies", ["/path/to/movies"]
    )
    assert result == test_library

    request = httpx_mock.get_request()
    payload = json.loads(request.content)
    assert payload["Name"] == "New Library"
    assert payload["CollectionType"] == "movies"
    assert len(payload["LibraryOptions"]["PathInfos"]) == 1
    assert payload["LibraryOptions"]["PathInfos"][0]["Path"] == "/path/to/movies"


@pytest.mark.asyncio
async def test_libraries_client_update_library_sends_updates(httpx_mock):
    test_library = {"Name": "Updated Library"}
    httpx_mock.add_response(
        method="POST",
        url="https://example.com/Library/VirtualFolders/lib1",
        json=test_library,
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    libraries_client = LibrariesClient(base_client)

    updates = {"Name": "Updated Library"}
    result = await libraries_client.update_library("lib1", updates)
    assert result == test_library

    request = httpx_mock.get_request()
    assert json.loads(request.content) == updates


@pytest.mark.asyncio
async def test_libraries_client_delete_library_sends_delete_request(httpx_mock):
    httpx_mock.add_response(
        method="DELETE",
        url="https://example.com/Library/VirtualFolders/lib1",
        json={"success": True},
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    libraries_client = LibrariesClient(base_client)

    await libraries_client.delete_library("lib1")

    request = httpx_mock.get_request()
    assert request.method == "DELETE"
    assert request.url == "https://example.com/Library/VirtualFolders/lib1"


@pytest.mark.asyncio
async def test_libraries_client_refresh_library_sends_refresh_request(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url="https://example.com/Library/VirtualFolders/lib1/Refresh",
        json={"success": True},
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    libraries_client = LibrariesClient(base_client)

    result = await libraries_client.refresh_library("lib1")
    assert result == {"success": True}

    request = httpx_mock.get_request()
    assert request.method == "POST"
    assert request.url == "https://example.com/Library/VirtualFolders/lib1/Refresh"


@pytest.mark.asyncio
async def test_libraries_client_get_library_items_returns_items(httpx_mock):
    test_items = {"Items": [{"Id": "item1", "Name": "Movie 1"}]}
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/Users/Items?ParentId=lib1&Recursive=true",
        json=test_items,
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    libraries_client = LibrariesClient(base_client)

    result = await libraries_client.get_library_items("lib1")
    assert result == [{"Id": "item1", "Name": "Movie 1"}]


@pytest.mark.asyncio
async def test_libraries_client_get_library_items_handles_non_dict_response(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/Users/Items?ParentId=lib1&Recursive=true",
        json=[{"unexpected": "response"}],
    )
    base_client = JellyfinClient("https://example.com", SecretStr("token"))
    libraries_client = LibrariesClient(base_client)

    result = await libraries_client.get_library_items("lib1")
    assert result == []
