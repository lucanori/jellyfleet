from jellyfleet.sync.diff import (
    DiffResult,
    compare_libraries,
    compare_server_configs,
    compare_user_configs,
    compare_user_policies,
    compare_users,
    compute_diff,
)


class TestDiffResult:
    def test_has_changes_with_no_changes(self):
        diff = DiffResult([], [], [])
        assert not diff.has_changes

    def test_has_changes_with_added_items(self):
        diff = DiffResult([{"id": "1"}], [], [])
        assert diff.has_changes

    def test_has_changes_with_removed_items(self):
        diff = DiffResult([], [{"id": "1"}], [])
        assert diff.has_changes

    def test_has_changes_with_modified_items(self):
        diff = DiffResult([], [], [({"id": "1"}, {"id": "1"})])
        assert diff.has_changes

    def test_total_changes(self):
        diff = DiffResult([{"id": "1"}], [{"id": "2"}], [({"id": "3"}, {"id": "3"})])
        assert diff.total_changes == 3


class TestComputeDiff:
    def test_empty_lists(self):
        result = compute_diff([], [], lambda x: x["id"])
        assert result.added == []
        assert result.removed == []
        assert result.modified == []

    def test_only_added_items(self):
        source = [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]
        target = []
        result = compute_diff(source, target, lambda x: x["id"])

        assert len(result.added) == 2
        assert result.removed == []
        assert result.modified == []
        added_names = [item["name"] for item in result.added]
        assert "Alice" in added_names
        assert "Bob" in added_names

    def test_only_removed_items(self):
        source = []
        target = [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]
        result = compute_diff(source, target, lambda x: x["id"])

        assert result.added == []
        assert len(result.removed) == 2
        assert result.modified == []
        removed_names = [item["name"] for item in result.removed]
        assert "Alice" in removed_names
        assert "Bob" in removed_names

    def test_no_changes(self):
        source = [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]
        target = [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]
        result = compute_diff(source, target, lambda x: x["id"])

        assert result.added == []
        assert result.removed == []
        assert result.modified == []

    def test_with_modifications(self):
        source = [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Robert"}]
        target = [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]

        def compare_func(a, b):
            return a["name"] == b["name"]

        result = compute_diff(source, target, lambda x: x["id"], compare_func)

        assert result.added == []
        assert result.removed == []
        assert len(result.modified) == 1
        assert result.modified[0][0]["name"] == "Robert"
        assert result.modified[0][1]["name"] == "Bob"


class TestCompareUsers:
    def test_identical_users(self):
        user1 = {
            "Name": "Alice",
            "HasPassword": True,
            "HasConfiguredPassword": True,
            "EnableAutoLogin": False,
            "LastLoginDate": "2023-01-01T00:00:00Z",
            "LastActivityDate": "2023-01-01T00:00:00Z",
        }
        user2 = user1.copy()
        assert compare_users(user1, user2)

    def test_different_names(self):
        user1 = {"Name": "Alice", "HasPassword": True}
        user2 = {"Name": "Bob", "HasPassword": True}
        assert not compare_users(user1, user2)

    def test_different_password_status(self):
        user1 = {"Name": "Alice", "HasPassword": True}
        user2 = {"Name": "Alice", "HasPassword": False}
        assert not compare_users(user1, user2)

    def test_missing_fields(self):
        user1 = {"Name": "Alice"}
        user2 = {"Name": "Alice", "HasPassword": False}
        assert not compare_users(user1, user2)


class TestCompareUserPolicies:
    def test_identical_policies(self):
        policy = {
            "IsAdministrator": False,
            "IsHidden": False,
            "IsDisabled": False,
            "EnableContentDeletion": True,
            "EnabledFolders": ["1", "2"],
        }
        assert compare_user_policies(policy, policy.copy())

    def test_different_admin_status(self):
        policy1 = {"IsAdministrator": True}
        policy2 = {"IsAdministrator": False}
        assert not compare_user_policies(policy1, policy2)

    def test_different_enabled_folders(self):
        policy1 = {"EnabledFolders": ["1", "2"]}
        policy2 = {"EnabledFolders": ["1", "3"]}
        assert not compare_user_policies(policy1, policy2)


class TestCompareUserConfigs:
    def test_identical_configs(self):
        config = {
            "AudioLanguagePreference": "en",
            "SubtitleMode": "Default",
            "DisplayMissingEpisodes": True,
        }
        assert compare_user_configs(config, config.copy())

    def test_different_audio_language(self):
        config1 = {"AudioLanguagePreference": "en"}
        config2 = {"AudioLanguagePreference": "es"}
        assert not compare_user_configs(config1, config2)


class TestCompareLibraries:
    def test_identical_libraries(self):
        library = {
            "Name": "Movies",
            "CollectionType": "movies",
            "LibraryOptions": {"PathInfos": [{"Path": "/movies"}]},
        }
        assert compare_libraries(library, library.copy())

    def test_different_names(self):
        lib1 = {"Name": "Movies", "CollectionType": "movies"}
        lib2 = {"Name": "TV Shows", "CollectionType": "movies"}
        assert not compare_libraries(lib1, lib2)

    def test_different_collection_types(self):
        lib1 = {"Name": "Media", "CollectionType": "movies"}
        lib2 = {"Name": "Media", "CollectionType": "tvshows"}
        assert not compare_libraries(lib1, lib2)


class TestCompareServerConfigs:
    def test_identical_configs(self):
        config = {
            "ServerName": "Test Server",
            "EnableUPnP": True,
            "HttpServerPortNumber": 8096,
        }
        assert compare_server_configs(config, config.copy())

    def test_different_server_names(self):
        config1 = {"ServerName": "Server 1"}
        config2 = {"ServerName": "Server 2"}
        assert not compare_server_configs(config1, config2)

    def test_ignores_unsyncable_fields(self):
        config1 = {"ServerName": "Test", "UnsyncableField": "value1"}
        config2 = {"ServerName": "Test", "UnsyncableField": "value2"}
        assert compare_server_configs(config1, config2)
