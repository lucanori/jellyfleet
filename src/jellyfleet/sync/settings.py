from __future__ import annotations

import logging
from typing import Any

from jellyfleet.jellyfin.client import JellyfinClient
from jellyfleet.jellyfin.settings import SettingsClient
from jellyfleet.sync.diff import compare_server_configs


class SettingsSync:
    def __init__(
        self, father_client: JellyfinClient, child_client: JellyfinClient
    ) -> None:
        self.father_client = father_client
        self.child_client = child_client
        self.father_settings = SettingsClient(father_client)
        self.child_settings = SettingsClient(child_client)
        self.logger = logging.getLogger(__name__)

    async def sync_server_settings(self, dry_run: bool = True) -> dict[str, Any]:
        self.logger.info("Starting server settings synchronization")

        try:
            father_config = await self.father_settings.get_server_configuration()
            child_config = await self.child_settings.get_server_configuration()

            results = {
                "modified": [],
                "errors": [],
            }

            if not compare_server_configs(father_config, child_config):
                syncable_config = self._extract_syncable_config(father_config)

                if not dry_run:
                    await self.child_settings.update_server_configuration(
                        syncable_config
                    )
                    results["modified"].append(
                        {
                            "action": "updated",
                            "fields_updated": list(syncable_config.keys()),
                        }
                    )
                    self.logger.info(
                        "Server settings updated with %d fields", len(syncable_config)
                    )
                else:
                    results["modified"].append(
                        {
                            "action": "would_update",
                            "fields_updated": list(syncable_config.keys()),
                        }
                    )
                    self.logger.info(
                        "Server settings would be updated with %d fields",
                        len(syncable_config),
                    )
            else:
                self.logger.info("Server settings are already in sync")

            return results

        except Exception as err:
            error_msg = f"Failed to sync server settings: {err}"
            self.logger.error(error_msg)
            return {"errors": [error_msg]}

    def _extract_syncable_config(self, config: dict[str, Any]) -> dict[str, Any]:
        syncable_fields = {
            "ServerName": config.get("ServerName"),
            "MetadataOptions": config.get("MetadataOptions", []),
            "MetadataNetworkMessage": config.get("MetadataNetworkMessage"),
            "EnableUPnP": config.get("EnableUPnP"),
            "PublicPort": config.get("PublicPort"),
            "HttpServerPortNumber": config.get("HttpServerPortNumber"),
            "HttpsPortNumber": config.get("HttpsPortNumber"),
            "EnableHttps": config.get("EnableHttps"),
            "EnableAutomaticPortMapping": config.get("EnableAutomaticPortMapping"),
            "RemoteIPFilter": config.get("RemoteIPFilter", []),
            "IsRemoteIPFilterBlacklist": config.get("IsRemoteIPFilterBlacklist"),
            "RemoteClientBitrateLimit": config.get("RemoteClientBitrateLimit"),
            "EnableSlowResponseWarning": config.get("EnableSlowResponseWarning"),
            "SlowResponseThresholdMs": config.get("SlowResponseThresholdMs"),
            "CorsPolicy": config.get("CorsPolicy"),
            "EnableCaseSensitiveItemIds": config.get("EnableCaseSensitiveItemIds"),
            "EnableSimpleDeveloperMode": config.get("EnableSimpleDeveloperMode"),
            "EnableDeveloperMode": config.get("EnableDeveloperMode"),
            "DisplaySpecialsWithinSeasons": config.get("DisplaySpecialsWithinSeasons"),
            "EnableExternalContentInSuggestions": config.get(
                "EnableExternalContentInSuggestions"
            ),
            "RequireHttps": config.get("RequireHttps"),
            "EnableNewOmdbSupport": config.get("EnableNewOmdbSupport"),
            "SaveMetadataHidden": config.get("SaveMetadataHidden"),
            "EnableStickerImages": config.get("EnableStickerImages"),
            "EnableChapterImageExtraction": config.get("EnableChapterImageExtraction"),
            "ExtractChapterImagesDuringLibraryScan": config.get(
                "ExtractChapterImagesDuringLibraryScan"
            ),
            "DownloadImagesInAdvance": config.get("DownloadImagesInAdvance"),
            "EnablePhotos": config.get("EnablePhotos"),
            "EnableRealtimeMonitor": config.get("EnableRealtimeMonitor"),
            "EnableAudioNormalization": config.get("EnableAudioNormalization"),
            "EnableThrottling": config.get("EnableThrottling"),
            "EnableHardwareDecoding": config.get("EnableHardwareDecoding"),
            "EnableSplashScreen": config.get("EnableSplashScreen"),
            "SkipDeserializationForBasicTypes": config.get(
                "SkipDeserializationForBasicTypes"
            ),
            "EnableTrickplayImageExtraction": config.get(
                "EnableTrickplayImageExtraction"
            ),
            "TrickplayImageInterval": config.get("TrickplayImageInterval"),
            "TrickplayImageResolution": config.get("TrickplayImageResolution"),
            "TrickplayImageQuality": config.get("TrickplayImageQuality"),
            "TrickplayImageBehavior": config.get("TrickplayImageBehavior"),
            "TrickplayImageProcessThreads": config.get("TrickplayImageProcessThreads"),
        }

        return {k: v for k, v in syncable_fields.items() if v is not None}
