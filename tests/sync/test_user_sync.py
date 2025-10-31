from unittest.mock import AsyncMock

import pytest

from jellyfleet.sync.users import UserSync


class TestUserSync:
    @pytest.fixture
    def mock_father_client(self):
        return AsyncMock()

    @pytest.fixture
    def mock_child_client(self):
        return AsyncMock()

    @pytest.fixture
    def user_sync(self, mock_father_client, mock_child_client):
        sync = UserSync(mock_father_client, mock_child_client)
        # Replace the UsersClient instances with mocks
        sync.father_users = AsyncMock()
        sync.child_users = AsyncMock()
        return sync

    @pytest.fixture
    def sample_father_users(self):
        return [
            {
                "Id": "father-1",
                "Name": "Alice",
                "HasPassword": True,
                "HasConfiguredPassword": True,
                "EnableAutoLogin": False,
                "LastLoginDate": "2023-01-01T00:00:00Z",
                "LastActivityDate": "2023-01-01T00:00:00Z",
            },
            {
                "Id": "father-2",
                "Name": "Bob",
                "HasPassword": False,
                "HasConfiguredPassword": False,
                "EnableAutoLogin": True,
                "LastLoginDate": None,
                "LastActivityDate": None,
            },
        ]

    @pytest.fixture
    def sample_child_users(self):
        return [
            {
                "Id": "child-1",
                "Name": "Alice",
                "HasPassword": True,
                "HasConfiguredPassword": True,
                "EnableAutoLogin": False,
                "LastLoginDate": "2023-01-01T00:00:00Z",
                "LastActivityDate": "2023-01-01T00:00:00Z",
            },
            {
                "Id": "child-3",
                "Name": "Charlie",
                "HasPassword": True,
                "HasConfiguredPassword": True,
                "EnableAutoLogin": False,
                "LastLoginDate": None,
                "LastActivityDate": None,
            },
        ]

    @pytest.mark.asyncio
    async def test_sync_users_dry_run(
        self,
        user_sync,
        mock_father_client,
        mock_child_client,
        sample_father_users,
        sample_child_users,
    ):
        user_sync.father_users.get_users.return_value = sample_father_users
        user_sync.child_users.get_users.return_value = sample_child_users

        result = await user_sync.sync_users(dry_run=True)

        assert len(result["added"]) == 1
        assert result["added"][0]["name"] == "Bob"
        assert result["added"][0]["action"] == "would_create"
        assert len(result["removed"]) == 1
        assert result["removed"][0]["name"] == "Charlie"
        assert result["removed"][0]["action"] == "would_delete"
        assert len(result["modified"]) == 0
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_sync_users_with_changes(
        self,
        user_sync,
        mock_father_client,
        mock_child_client,
        sample_father_users,
        sample_child_users,
    ):
        user_sync.father_users.get_users = AsyncMock(return_value=sample_father_users)
        user_sync.child_users.get_users = AsyncMock(return_value=sample_child_users)

        user_sync.child_users.create_user = AsyncMock(return_value={"Id": "new-bob-id"})
        user_sync.child_users.delete_user = AsyncMock(return_value=None)

        result = await user_sync.sync_users(dry_run=False)

        assert len(result["added"]) == 1
        assert result["added"][0]["name"] == "Bob"
        assert result["added"][0]["action"] == "created"
        assert result["added"][0]["id"] == "new-bob-id"
        assert len(result["removed"]) == 1
        assert result["removed"][0]["name"] == "Charlie"
        assert result["removed"][0]["action"] == "deleted"

        user_sync.child_users.create_user.assert_called_once_with(
            "Bob", "temp_password_123"
        )
        user_sync.child_users.delete_user.assert_called_once_with("child-3")

    @pytest.mark.asyncio
    async def test_sync_users_with_modifications(
        self, user_sync, mock_father_client, mock_child_client
    ):
        father_users = [
            {
                "Id": "father-1",
                "Name": "Alice",
                "HasPassword": True,
                "EnableAutoLogin": True,
            }
        ]
        child_users = [
            {
                "Id": "child-1",
                "Name": "Alice",
                "HasPassword": True,
                "EnableAutoLogin": False,
            }
        ]

        user_sync.father_users.get_users = AsyncMock(return_value=father_users)
        user_sync.child_users.get_users = AsyncMock(return_value=child_users)

        # Configure policy and config mocks to return different values
        user_sync.father_users.get_user_policy = AsyncMock(
            return_value={"IsAdministrator": True}
        )
        user_sync.child_users.get_user_policy = AsyncMock(
            return_value={"IsAdministrator": False}
        )
        user_sync.father_users.get_user_configuration = AsyncMock(
            return_value={"AudioLanguagePreference": "en"}
        )
        user_sync.child_users.get_user_configuration = AsyncMock(
            return_value={"AudioLanguagePreference": "es"}
        )

        mock_child_client.update_user = AsyncMock(return_value=None)
        mock_child_client.update_user_policy = AsyncMock(return_value=None)
        mock_child_client.update_user_configuration = AsyncMock(return_value=None)

        result = await user_sync.sync_users(dry_run=False)

        # Should have 3 modifications: user data, policy, and configuration
        assert len(result["modified"]) == 3

        # Check the user data modification
        user_mod = next(m for m in result["modified"] if "updates" in m)
        assert user_mod["name"] == "Alice"
        assert user_mod["updates"]["EnableAutoLogin"] is True

        user_sync.child_users.update_user.assert_called_once_with(
            "child-1", {"EnableAutoLogin": True}
        )

    @pytest.mark.asyncio
    async def test_sync_user_policies(
        self, user_sync, mock_father_client, mock_child_client
    ):
        father_user = {"Id": "father-1", "Name": "Alice"}
        child_user = {"Id": "child-1", "Name": "Alice"}

        father_policy = {"IsAdministrator": True, "EnableContentDeletion": True}
        child_policy = {"IsAdministrator": False, "EnableContentDeletion": True}

        user_sync.father_users.get_user_policy = AsyncMock(return_value=father_policy)
        user_sync.child_users.get_user_policy = AsyncMock(return_value=child_policy)
        mock_child_client.update_user_policy = AsyncMock(return_value=None)

        results = {"errors": [], "modified": []}

        await user_sync._sync_user_policies(father_user, child_user, False, results)

        assert len(results["modified"]) == 1
        assert results["modified"][0]["type"] == "policy"
        assert results["modified"][0]["action"] == "updated"

        user_sync.child_users.update_user_policy.assert_called_once_with(
            "child-1", father_policy
        )

    @pytest.mark.asyncio
    async def test_sync_user_configurations(
        self, user_sync, mock_father_client, mock_child_client
    ):
        father_user = {"Id": "father-1", "Name": "Alice"}
        child_user = {"Id": "child-1", "Name": "Alice"}

        father_config = {"AudioLanguagePreference": "en", "SubtitleMode": "Default"}
        child_config = {"AudioLanguagePreference": "es", "SubtitleMode": "Default"}

        user_sync.father_users.get_user_configuration = AsyncMock(
            return_value=father_config
        )
        user_sync.child_users.get_user_configuration = AsyncMock(
            return_value=child_config
        )
        mock_child_client.update_user_configuration = AsyncMock(return_value=None)

        results = {"errors": [], "modified": []}

        await user_sync._sync_user_configurations(
            father_user, child_user, False, results
        )

        assert len(results["modified"]) == 1
        assert results["modified"][0]["type"] == "configuration"
        assert results["modified"][0]["action"] == "updated"

        user_sync.child_users.update_user_configuration.assert_called_once_with(
            "child-1", father_config
        )

    @pytest.mark.asyncio
    async def test_sync_users_with_errors(
        self, user_sync, mock_father_client, mock_child_client
    ):
        user_sync.father_users.get_users = AsyncMock(
            return_value=[{"Id": "father-1", "Name": "Alice"}]
        )
        user_sync.child_users.get_users = AsyncMock(return_value=[])
        user_sync.child_users.create_user = AsyncMock(
            side_effect=Exception("API Error")
        )

        result = await user_sync.sync_users(dry_run=False)

        assert len(result["added"]) == 0
        assert len(result["errors"]) == 1
        assert "Failed to add user Alice" in result["errors"][0]
