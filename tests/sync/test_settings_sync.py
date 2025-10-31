from unittest.mock import AsyncMock

import pytest

from jellyfleet.sync.settings import SettingsSync


class TestSettingsSync:
    @pytest.fixture
    def mock_father_client(self):
        return AsyncMock()

    @pytest.fixture
    def mock_child_client(self):
        return AsyncMock()

    @pytest.fixture
    def settings_sync(self, mock_father_client, mock_child_client):
        sync = SettingsSync(mock_father_client, mock_child_client)
        sync.father_settings = AsyncMock()
        sync.child_settings = AsyncMock()
        return sync

    @pytest.fixture
    def sample_father_config(self):
        return {
            "ServerName": "Father Server",
            "EnableUPnP": True,
            "HttpServerPortNumber": 8096,
            "HttpsPortNumber": 8097,
            "EnableHttps": False,
            "EnableAutomaticPortMapping": True,
            "RemoteClientBitrateLimit": 100000000,
            "EnableSlowResponseWarning": True,
            "SlowResponseThresholdMs": 500,
            "CorsPolicy": "",
            "EnableCaseSensitiveItemIds": False,
            "EnableSimpleDeveloperMode": False,
            "EnableDeveloperMode": False,
            "DisplaySpecialsWithinSeasons": True,
            "EnableExternalContentInSuggestions": False,
            "RequireHttps": False,
            "EnableNewOmdbSupport": True,
            "SaveMetadataHidden": False,
            "EnableStickerImages": True,
            "EnableChapterImageExtraction": True,
            "ExtractChapterImagesDuringLibraryScan": False,
            "DownloadImagesInAdvance": True,
            "EnablePhotos": True,
            "EnableRealtimeMonitor": True,
            "EnableAudioNormalization": False,
            "EnableThrottling": False,
            "EnableHardwareDecoding": True,
            "EnableSplashScreen": True,
            "SkipDeserializationForBasicTypes": False,
            "EnableTrickplayImageExtraction": False,
            "TrickplayImageInterval": 5,
            "TrickplayImageResolution": 360,
            "TrickplayImageQuality": 50,
            "TrickplayImageBehavior": "Default",
            "TrickplayImageProcessThreads": 1,
            "UnsyncableField": "should_be_ignored",
        }

    @pytest.fixture
    def sample_child_config(self):
        return {
            "ServerName": "Child Server",
            "EnableUPnP": False,
            "HttpServerPortNumber": 8096,
            "HttpsPortNumber": 8097,
            "EnableHttps": False,
            "EnableAutomaticPortMapping": False,
            "RemoteClientBitrateLimit": 50000000,
            "EnableSlowResponseWarning": False,
            "SlowResponseThresholdMs": 1000,
            "CorsPolicy": "",
            "EnableCaseSensitiveItemIds": False,
            "EnableSimpleDeveloperMode": False,
            "EnableDeveloperMode": False,
            "DisplaySpecialsWithinSeasons": False,
            "EnableExternalContentInSuggestions": False,
            "RequireHttps": False,
            "EnableNewOmdbSupport": True,
            "SaveMetadataHidden": False,
            "EnableStickerImages": False,
            "EnableChapterImageExtraction": False,
            "ExtractChapterImagesDuringLibraryScan": False,
            "DownloadImagesInAdvance": False,
            "EnablePhotos": False,
            "EnableRealtimeMonitor": False,
            "EnableAudioNormalization": False,
            "EnableThrottling": False,
            "EnableHardwareDecoding": False,
            "EnableSplashScreen": False,
            "SkipDeserializationForBasicTypes": False,
            "EnableTrickplayImageExtraction": False,
            "TrickplayImageInterval": 5,
            "TrickplayImageResolution": 360,
            "TrickplayImageQuality": 50,
            "TrickplayImageBehavior": "Default",
            "TrickplayImageProcessThreads": 1,
            "UnsyncableField": "should_be_ignored",
        }

    @pytest.mark.asyncio
    async def test_sync_server_settings_no_changes(
        self, settings_sync, mock_father_client, mock_child_client, sample_father_config
    ):
        settings_sync.father_settings.get_server_configuration.return_value = (
            sample_father_config
        )
        settings_sync.child_settings.get_server_configuration.return_value = (
            sample_father_config
        )

        result = await settings_sync.sync_server_settings(dry_run=True)

        assert len(result["modified"]) == 0
        assert len(result["errors"]) == 0

        settings_sync.father_settings.get_server_configuration.assert_called_once()
        settings_sync.child_settings.get_server_configuration.assert_called_once()
        settings_sync.child_settings.update_server_configuration.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_server_settings_with_changes_dry_run(
        self,
        settings_sync,
        mock_father_client,
        mock_child_client,
        sample_father_config,
        sample_child_config,
    ):
        settings_sync.father_settings.get_server_configuration.return_value = (
            sample_father_config
        )
        settings_sync.child_settings.get_server_configuration.return_value = (
            sample_child_config
        )

        result = await settings_sync.sync_server_settings(dry_run=True)

        assert len(result["modified"]) == 1
        assert result["modified"][0]["action"] == "would_update"
        assert "ServerName" in result["modified"][0]["fields_updated"]
        assert "EnableUPnP" in result["modified"][0]["fields_updated"]
        assert len(result["errors"]) == 0

        settings_sync.child_settings.update_server_configuration.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_server_settings_with_changes_apply(
        self,
        settings_sync,
        mock_father_client,
        mock_child_client,
        sample_father_config,
        sample_child_config,
    ):
        settings_sync.father_settings.get_server_configuration.return_value = (
            sample_father_config
        )
        settings_sync.child_settings.get_server_configuration.return_value = (
            sample_child_config
        )
        mock_child_client.update_server_configuration.return_value = None

        result = await settings_sync.sync_server_settings(dry_run=False)

        assert len(result["modified"]) == 1
        assert result["modified"][0]["action"] == "updated"
        assert "ServerName" in result["modified"][0]["fields_updated"]
        assert "EnableUPnP" in result["modified"][0]["fields_updated"]
        assert len(result["errors"]) == 0

        settings_sync.child_settings.update_server_configuration.assert_called_once()

        call_args = settings_sync.child_settings.update_server_configuration.call_args[0][0]
        assert call_args["ServerName"] == "Father Server"
        assert call_args["EnableUPnP"] is True
        assert "UnsyncableField" not in call_args

    @pytest.mark.asyncio
    async def test_sync_server_settings_with_error(
        self, settings_sync, mock_father_client, mock_child_client
    ):
        settings_sync.father_settings.get_server_configuration.side_effect = Exception(
            "API Error"
        )

        result = await settings_sync.sync_server_settings(dry_run=True)

        # When there's an error, only errors key is returned
        assert "modified" not in result
        assert len(result["errors"]) == 1
        assert "Failed to sync server settings" in result["errors"][0]

    def test_extract_syncable_config(self, settings_sync, sample_father_config):
        syncable_config = settings_sync._extract_syncable_config(sample_father_config)

        assert "ServerName" in syncable_config
        assert "EnableUPnP" in syncable_config
        assert "UnsyncableField" not in syncable_config
        assert syncable_config["ServerName"] == "Father Server"
        assert syncable_config["EnableUPnP"] is True

    def test_extract_syncable_config_filters_none_values(self, settings_sync):
        config_with_nones = {
            "ServerName": "Test Server",
            "EnableUPnP": None,
            "HttpServerPortNumber": 8096,
            "EnableHttps": None,
        }

        syncable_config = settings_sync._extract_syncable_config(config_with_nones)

        assert "ServerName" in syncable_config
        assert "HttpServerPortNumber" in syncable_config
        assert "EnableUPnP" not in syncable_config
        assert "EnableHttps" not in syncable_config
