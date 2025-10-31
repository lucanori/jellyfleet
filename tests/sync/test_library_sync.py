from unittest.mock import AsyncMock

import pytest

from jellyfleet.sync.libraries import LibrarySync


class TestLibrarySync:
    @pytest.fixture
    def mock_father_client(self):
        return AsyncMock()

    @pytest.fixture
    def mock_child_client(self):
        return AsyncMock()

    @pytest.fixture
    def library_sync(self, mock_father_client, mock_child_client):
        sync = LibrarySync(mock_father_client, mock_child_client)
        sync.father_libraries = AsyncMock()
        sync.child_libraries = AsyncMock()
        return sync

    @pytest.fixture
    def sample_father_libraries(self):
        return [
            {
                "Id": "father-1",
                "Name": "Movies",
                "CollectionType": "movies",
                "LibraryOptions": {
                    "PathInfos": [
                        {"Path": "/media/movies"},
                        {"Path": "/media/movies2"},
                    ]
                },
            },
            {
                "Id": "father-2",
                "Name": "TV Shows",
                "CollectionType": "tvshows",
                "LibraryOptions": {
                    "PathInfos": [
                        {"Path": "/media/tvshows"},
                    ]
                },
            },
        ]

    @pytest.fixture
    def sample_child_libraries(self):
        return [
            {
                "Id": "child-1",
                "Name": "Movies",
                "CollectionType": "movies",
                "LibraryOptions": {
                    "PathInfos": [
                        {"Path": "/media/movies"},
                    ]
                },
            },
            {
                "Id": "child-3",
                "Name": "Music",
                "CollectionType": "music",
                "LibraryOptions": {
                    "PathInfos": [
                        {"Path": "/media/music"},
                    ]
                },
            },
        ]

    @pytest.mark.asyncio
    async def test_sync_libraries_dry_run(
        self,
        library_sync,
        mock_father_client,
        mock_child_client,
        sample_father_libraries,
        sample_child_libraries,
    ):
        library_sync.father_libraries.get_libraries.return_value = (
            sample_father_libraries
        )
        library_sync.child_libraries.get_libraries.return_value = sample_child_libraries

        result = await library_sync.sync_libraries(dry_run=True)

        assert len(result["added"]) == 1
        assert result["added"][0]["name"] == "TV Shows"
        assert result["added"][0]["action"] == "would_create"
        assert result["added"][0]["collection_type"] == "tvshows"
        assert "/media/tvshows" in result["added"][0]["paths"]

        assert len(result["removed"]) == 1
        assert result["removed"][0]["name"] == "Music"
        assert result["removed"][0]["action"] == "would_delete"

        assert len(result["modified"]) == 1
        assert result["modified"][0]["name"] == "Movies"
        assert result["modified"][0]["action"] == "would_update"

        assert len(result["errors"]) == 0

        library_sync.father_libraries.get_libraries.assert_called_once()
        library_sync.child_libraries.get_libraries.assert_called_once()
        mock_child_client.create_library.assert_not_called()
        mock_child_client.delete_library.assert_not_called()
        mock_child_client.update_library.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_libraries_with_changes_apply(
        self,
        library_sync,
        mock_father_client,
        mock_child_client,
        sample_father_libraries,
        sample_child_libraries,
    ):
        library_sync.father_libraries.get_libraries = AsyncMock(return_value=sample_father_libraries)
        library_sync.child_libraries.get_libraries = AsyncMock(return_value=sample_child_libraries)

        library_sync.child_libraries.create_library = AsyncMock(return_value={"Id": "new-tvshows-id"})
        library_sync.child_libraries.delete_library = AsyncMock(return_value=None)
        library_sync.child_libraries.update_library = AsyncMock(return_value=None)

        result = await library_sync.sync_libraries(dry_run=False)

        assert len(result["added"]) == 1
        assert result["added"][0]["name"] == "TV Shows"
        assert result["added"][0]["action"] == "created"
        assert result["added"][0]["id"] == "new-tvshows-id"

        assert len(result["removed"]) == 1
        assert result["removed"][0]["name"] == "Music"
        assert result["removed"][0]["action"] == "deleted"

        assert len(result["modified"]) == 1
        assert result["modified"][0]["name"] == "Movies"
        assert result["modified"][0]["action"] == "updated"

        library_sync.child_libraries.create_library.assert_called_once_with(
            "TV Shows", "tvshows", ["/media/tvshows"]
        )
        library_sync.child_libraries.delete_library.assert_called_once_with("child-3")
        library_sync.child_libraries.update_library.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_libraries_no_changes(
        self,
        library_sync,
        mock_father_client,
        mock_child_client,
        sample_father_libraries,
    ):
        mock_father_client.get_libraries.return_value = sample_father_libraries
        mock_child_client.get_libraries.return_value = sample_father_libraries

        result = await library_sync.sync_libraries(dry_run=True)

        assert len(result["added"]) == 0
        assert len(result["removed"]) == 0
        assert len(result["modified"]) == 0
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_sync_libraries_with_errors(
        self, library_sync, mock_father_client, mock_child_client
    ):
        library_sync.father_libraries.get_libraries.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            await library_sync.sync_libraries(dry_run=True)

    def test_extract_paths_from_library(self, library_sync):
        library = {
            "Name": "Movies",
            "LibraryOptions": {
                "PathInfos": [
                    {"Path": "/media/movies"},
                    {"Path": "/media/movies2"},
                    {"Path": ""},
                ]
            },
        }

        paths = library_sync._extract_paths_from_library(library)

        assert len(paths) == 2
        assert "/media/movies" in paths
        assert "/media/movies2" in paths

    def test_extract_paths_from_library_no_paths(self, library_sync):
        library = {
            "Name": "Empty",
            "LibraryOptions": {"PathInfos": []},
        }

        paths = library_sync._extract_paths_from_library(library)

        assert len(paths) == 0

    def test_extract_paths_from_library_no_library_options(self, library_sync):
        library = {"Name": "No Options"}

        paths = library_sync._extract_paths_from_library(library)

        assert len(paths) == 0

    def test_extract_library_updates(self, library_sync):
        father_lib = {
            "Name": "Movies",
            "CollectionType": "movies",
            "LibraryOptions": {
                "PathInfos": [
                    {"Path": "/media/movies"},
                    {"Path": "/media/movies2"},
                ]
            },
        }
        child_lib = {
            "Name": "Movies",
            "CollectionType": "tvshows",
            "LibraryOptions": {
                "PathInfos": [
                    {"Path": "/media/movies"},
                ]
            },
        }

        updates = library_sync._extract_library_updates(father_lib, child_lib)

        assert "CollectionType" in updates
        assert updates["CollectionType"] == "movies"
        assert "LibraryOptions" in updates
        assert len(updates["LibraryOptions"]["PathInfos"]) == 2

    def test_extract_library_updates_no_changes(self, library_sync):
        lib = {
            "Name": "Movies",
            "CollectionType": "movies",
            "LibraryOptions": {
                "PathInfos": [
                    {"Path": "/media/movies"},
                ]
            },
        }

        updates = library_sync._extract_library_updates(lib, lib)

        assert len(updates) == 0
