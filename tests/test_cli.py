from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from jellyfleet.cli import cli


class TestCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def config_file(self, tmp_path):
        config_content = """
servers:
  father:
    url: "http://father.jellyfin.local:8096"
    token: "father-api-key-here"
  child:
    url: "http://child.jellyfin.local:8097"
    token: "child-api-key-here"

combinations:
  - name: main-sync
    father: father
    children:
      - server: child
        domains:
          - users
          - settings
          - libraries

scheduler:
  cron: "0 */6 * * *"

runtime:
  dry_run: true
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        return str(config_file)

    def test_validate_command_success(self, runner, config_file):
        with patch("jellyfleet.cli.load_config") as mock_load:
            mock_config = MagicMock()
            mock_config.combinations = [
                MagicMock(
                    name="test-combo",
                    children=[MagicMock(domains=["users", "settings"])],
                )
            ]
            mock_load.return_value = mock_config

            result = runner.invoke(cli, ["-c", config_file, "validate"])

            assert result.exit_code == 0
            assert "✓ Configuration file is valid" in result.output
            assert "✓ Found 1 combination(s)" in result.output

    def test_validate_command_no_config(self, runner):
        result = runner.invoke(cli, ["validate"])

        assert result.exit_code == 1
        assert "Error: Configuration file is required" in result.output

    def test_validate_command_invalid_config(self, runner, config_file):
        with patch("jellyfleet.cli.load_config") as mock_load:
            mock_load.side_effect = Exception("Invalid config")

            result = runner.invoke(cli, ["-c", config_file, "validate"])

            assert result.exit_code == 1
            assert "✗ Configuration validation failed" in result.output

    @patch("jellyfleet.cli.create_database_engine")
    @patch("jellyfleet.cli.create_session_factory")
    @patch("jellyfleet.cli.load_config")
    @patch("jellyfleet.cli.JellyfinClient")
    @patch("jellyfleet.cli.SyncOrchestrator")
    def test_sync_command_dry_run_success(
        self,
        mock_orchestrator,
        mock_client,
        mock_load,
        mock_session_factory,
        mock_engine,
        runner,
        config_file,
    ):
        from jellyfleet.config.models import Domain

        mock_config = MagicMock()
        combo_mock = MagicMock()
        combo_mock.name = "main-sync"
        combo_mock.father = "father"
        combo_mock.children = [
            MagicMock(
                server="child",
                domains=[Domain.users, Domain.settings, Domain.libraries],
            )
        ]
        mock_config.combinations = [combo_mock]

        father_token = MagicMock()
        father_token.get_secret_value.return_value = "father-token"
        child_token = MagicMock()
        child_token.get_secret_value.return_value = "child-token"

        mock_config.servers = {
            "father": MagicMock(
                url="http://father.jellyfin.local:8096", token=father_token
            ),
            "child": MagicMock(
                url="http://child.jellyfin.local:8097", token=child_token
            ),
        }
        mock_load.return_value = mock_config

        mock_session = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session

        mock_sync_run = MagicMock()
        mock_sync_run.status = "completed"
        mock_sync_run.actions_count = 0
        mock_sync_run.details = "No changes needed"
        mock_sync_run.error_message = None

        mock_orchestrator_instance = AsyncMock()
        mock_orchestrator_instance.run_sync.return_value = mock_sync_run
        mock_orchestrator.return_value = mock_orchestrator_instance

        result = runner.invoke(cli, ["-c", config_file, "sync", "--dry-run"])

        assert result.exit_code == 0
        assert "Status: completed" in result.output
        assert "Actions: 0" in result.output

    @patch("jellyfleet.cli.create_database_engine")
    @patch("jellyfleet.cli.create_session_factory")
    @patch("jellyfleet.cli.load_config")
    def test_sync_command_no_config(
        self, mock_load, mock_session_factory, mock_engine, runner
    ):
        result = runner.invoke(cli, ["sync"])

        assert result.exit_code == 1
        assert "Error: Configuration file is required" in result.output

    @patch("jellyfleet.cli.create_database_engine")
    @patch("jellyfleet.cli.create_session_factory")
    @patch("jellyfleet.cli.load_config")
    def test_status_command_no_runs(
        self, mock_load, mock_session_factory, mock_engine, runner, config_file
    ):
        mock_session = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session

        with patch("jellyfleet.cli.SyncRepository") as mock_repo:
            mock_repo_instance = MagicMock()
            mock_repo_instance.get_recent_sync_runs.return_value = []
            mock_repo.return_value = mock_repo_instance

            result = runner.invoke(cli, ["-c", config_file, "status"])

            assert result.exit_code == 0
            assert "No sync runs found" in result.output

    @patch("jellyfleet.cli.create_database_engine")
    @patch("jellyfleet.cli.create_session_factory")
    @patch("jellyfleet.cli.load_config")
    def test_status_command_with_runs(
        self, mock_load, mock_session_factory, mock_engine, runner, config_file
    ):
        mock_session = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session

        with patch("jellyfleet.cli.SyncRepository") as mock_repo:
            mock_sync_run = MagicMock()
            mock_sync_run.started_at = "2025-10-31 17:30:00"
            mock_sync_run.combination_name = "main-sync-child"
            mock_sync_run.status = "completed"
            mock_sync_run.actions_count = 5
            mock_sync_run.error_message = None

            mock_repo_instance = MagicMock()
            mock_repo_instance.get_recent_sync_runs.return_value = [mock_sync_run]
            mock_repo.return_value = mock_repo_instance

            result = runner.invoke(cli, ["-c", config_file, "status"])

            assert result.exit_code == 0
            assert "Recent 1 sync runs:" in result.output
            assert (
                "✓ 2025-10-31 17:30:00 | main-sync-child | completed | 5 actions"
                in result.output
            )

    def test_status_command_no_config(self, runner):
        result = runner.invoke(cli, ["status"])

        assert result.exit_code == 1
        assert "Error: Configuration file is required" in result.output

    def test_schedule_command(self, runner, config_file):
        result = runner.invoke(cli, ["-c", config_file, "schedule", "--help"])

        assert result.exit_code == 0
        assert "Start the scheduler for automatic sync runs" in result.output

    def test_schedule_command_no_config(self, runner):
        result = runner.invoke(cli, ["schedule"])

        assert result.exit_code == 1
        assert "Error: Configuration file is required" in result.output

    def test_help_command(self, runner):
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "sync" in result.output
        assert "validate" in result.output
        assert "status" in result.output
        assert "schedule" in result.output
