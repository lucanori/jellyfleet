from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from jellyfleet.db.models import SyncRun
from jellyfleet.sync.orchestrator import SyncOrchestrator


class TestSyncOrchestrator:
    @pytest.fixture
    def mock_father_client(self):
        return AsyncMock()

    @pytest.fixture
    def mock_child_client(self):
        return AsyncMock()

    @pytest.fixture
    def mock_repository(self):
        repository = Mock()
        sync_run = MagicMock()
        sync_run.id = 1
        repository.create_sync_run.return_value = sync_run
        repository.get_sync_run.return_value = MagicMock(spec=SyncRun)
        return repository

    @pytest.fixture
    def orchestrator(self, mock_father_client, mock_child_client, mock_repository):
        orchestrator = SyncOrchestrator(
            father_client=mock_father_client,
            child_client=mock_child_client,
            repository=mock_repository,
            combination_name="test-combo",
            domains=["users", "settings", "libraries"],
        )

        orchestrator.settings_sync = AsyncMock()
        orchestrator.user_sync = AsyncMock()
        orchestrator.library_sync = AsyncMock()

        return orchestrator

    @pytest.mark.asyncio
    async def test_run_sync_dry_run_success(self, orchestrator, mock_repository):
        mock_repository.create_sync_run.return_value.id = 1
        mock_repository.get_sync_run.return_value = MagicMock(spec=SyncRun)

        result = await orchestrator.run_sync(dry_run=True)

        assert result is not None
        mock_repository.create_sync_run.assert_called_once_with(
            combination_name="test-combo",
            father_server=orchestrator.father_server,
            child_server=orchestrator.child_server,
            domains="users,settings,libraries",
            dry_run=True,
        )
        mock_repository.complete_sync_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_sync_apply_changes_success(self, orchestrator, mock_repository):
        mock_repository.create_sync_run.return_value.id = 1
        mock_repository.get_sync_run.return_value = MagicMock(spec=SyncRun)

        result = await orchestrator.run_sync(dry_run=False)

        assert result is not None
        mock_repository.create_sync_run.assert_called_once_with(
            combination_name="test-combo",
            father_server=orchestrator.father_server,
            child_server=orchestrator.child_server,
            domains="users,settings,libraries",
            dry_run=False,
        )
        mock_repository.complete_sync_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_sync_with_error(self, orchestrator, mock_repository):
        orchestrator.settings_sync.sync_server_settings.side_effect = Exception(
            "Sync failed"
        )

        mock_repository.create_sync_run.return_value.id = 1
        mock_repository.get_sync_run.return_value = MagicMock(spec=SyncRun)

        # The orchestrator catches individual sync errors and includes them in results
        # so the overall sync should complete successfully with errors in the results
        result = await orchestrator.run_sync(dry_run=True)

        mock_repository.complete_sync_run.assert_called_once()
        call_args = mock_repository.complete_sync_run.call_args[1]
        assert call_args["status"] == "completed"

        # Check that the error was captured in the details passed to complete_sync_run
        details = call_args["details"]
        assert "Settings: 0 actions, 1 errors" in details

    @pytest.mark.asyncio
    async def test_perform_sync_all_domains_success(self, orchestrator):
        orchestrator.settings_sync.sync_server_settings.return_value = {"modified": []}
        orchestrator.user_sync.sync_users.return_value = {
            "added": [],
            "removed": [],
            "modified": [],
            "errors": [],
        }
        orchestrator.library_sync.sync_libraries.return_value = {
            "added": [],
            "removed": [],
            "modified": [],
            "errors": [],
        }

        result = await orchestrator._perform_sync(dry_run=True)

        assert "start_time" in result
        assert "end_time" in result
        assert "users" in result
        assert "settings" in result
        assert "libraries" in result

        orchestrator.settings_sync.sync_server_settings.assert_called_once_with(True)
        orchestrator.user_sync.sync_users.assert_called_once_with(True)
        orchestrator.library_sync.sync_libraries.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_perform_sync_with_domain_errors(self, orchestrator):
        orchestrator.settings_sync.sync_server_settings.side_effect = Exception(
            "Settings error"
        )
        orchestrator.user_sync.sync_users.return_value = {
            "added": [],
            "removed": [],
            "modified": [],
            "errors": [],
        }
        orchestrator.library_sync.sync_libraries.return_value = {
            "added": [],
            "removed": [],
            "modified": [],
            "errors": [],
        }

        result = await orchestrator._perform_sync(dry_run=True)

        assert "errors" in result["settings"]
        assert "Settings error" in result["settings"]["errors"][0]
        assert "users" in result
        assert "libraries" in result

    def test_format_results_no_changes(self, orchestrator):
        results = {
            "users": {"added": [], "removed": [], "modified": [], "errors": []},
            "settings": {"modified": [], "errors": []},
            "libraries": {"added": [], "removed": [], "modified": [], "errors": []},
            "start_time": "2023-01-01T00:00:00Z",
            "end_time": "2023-01-01T00:01:00Z",
        }

        formatted = orchestrator._format_results(results)

        assert formatted == "No changes needed"

    def test_format_results_with_changes(self, orchestrator):
        results = {
            "users": {
                "added": [{"name": "Alice"}],
                "removed": [],
                "modified": [],
                "errors": [],
            },
            "settings": {"modified": [{"action": "updated"}], "errors": []},
            "libraries": {
                "added": [],
                "removed": [{"name": "Old Lib"}],
                "modified": [],
                "errors": [],
            },
            "start_time": "2023-01-01T00:00:00Z",
            "end_time": "2023-01-01T00:01:00Z",
        }

        formatted = orchestrator._format_results(results)

        assert "Users: 1 actions, 0 errors" in formatted
        assert "Settings: 1 actions, 0 errors" in formatted
        assert "Libraries: 1 actions, 0 errors" in formatted

    def test_count_actions_no_changes(self, orchestrator):
        results = {
            "users": {"added": [], "removed": [], "modified": [], "errors": []},
            "settings": {"modified": [], "errors": []},
            "libraries": {"added": [], "removed": [], "modified": [], "errors": []},
        }

        count = orchestrator._count_actions(results)

        assert count == 0

    def test_count_actions_with_changes(self, orchestrator):
        results = {
            "users": {
                "added": [{"name": "Alice"}],
                "removed": [{"name": "Bob"}],
                "modified": [],
                "errors": [],
            },
            "settings": {"modified": [{"action": "updated"}], "errors": []},
            "libraries": {
                "added": [],
                "removed": [],
                "modified": [{"name": "Movies"}],
                "errors": [],
            },
        }

        count = orchestrator._count_actions(results)

        assert count == 4

    def test_count_actions_ignores_errors(self, orchestrator):
        results = {
            "users": {
                "added": [],
                "removed": [],
                "modified": [],
                "errors": ["Error 1", "Error 2"],
            },
            "settings": {"modified": [], "errors": ["Error 3"]},
            "libraries": {"added": [], "removed": [], "modified": [], "errors": []},
        }

        count = orchestrator._count_actions(results)

        assert count == 0
