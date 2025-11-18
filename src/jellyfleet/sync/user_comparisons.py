from __future__ import annotations

from typing import Any


def compare_users(user1: dict[str, Any], user2: dict[str, Any]) -> bool:
    user1_fields = {
        "Name": user1.get("Name"),
        "HasPassword": user1.get("HasPassword"),
        "HasConfiguredPassword": user1.get("HasConfiguredPassword"),
        "EnableAutoLogin": user1.get("EnableAutoLogin"),
        "LastLoginDate": user1.get("LastLoginDate"),
        "LastActivityDate": user1.get("LastActivityDate"),
    }
    user2_fields = {
        "Name": user2.get("Name"),
        "HasPassword": user2.get("HasPassword"),
        "HasConfiguredPassword": user2.get("HasConfiguredPassword"),
        "EnableAutoLogin": user2.get("EnableAutoLogin"),
        "LastLoginDate": user2.get("LastLoginDate"),
        "LastActivityDate": user2.get("LastActivityDate"),
    }
    return user1_fields == user2_fields


def compare_user_policies(policy1: dict[str, Any], policy2: dict[str, Any]) -> bool:
    policy_fields = [
        "IsAdministrator",
        "IsHidden",
        "IsDisabled",
        "EnableContentDeletion",
        "EnableContentDownloading",
        "EnableSyncTranscoding",
        "EnableMediaPlayback",
        "EnableAudioPlaybackTranscoding",
        "EnableVideoPlaybackTranscoding",
        "EnablePlaybackRemuxing",
        "ForceRemoteSourceTranscoding",
        "EnableLiveTvManagement",
        "EnableLiveTvAccess",
        "EnableMediaConversion",
        "EnableChannelManagement",
        "EnableChannelAccess",
        "EnableDeviceAccess",
        "EnableAllChannels",
        "EnableAllDevices",
        "EnableSharedDeviceControl",
        "EnableRemoteControlOfOtherUsers",
        "EnableLiveTvRecording",
        "EnableLiveTvPlayback",
        "EnableLiveTvPlaybackTranscoding",
        "EnableCollectionManagement",
        "EnableSubtitleManagement",
        "EnableLyricManagement",
        "EnableAllFolders",
        "EnableUserPreferenceAccess",
        "Tagline",
        "LoginAttemptsBeforeLockout",
        "MaxActiveSessions",
        "EnablePublicSharing",
        "RemoteClientBitrateLimit",
        "AuthenticationProviderId",
        "PasswordResetProviderId",
    ]

    list_fields = [
        "EnabledFolders",
        "EnabledChannels",
        "EnabledDevices",
        "BlockedChannels",
        "BlockedMediaFolders",
        "BlockedTags",
        "AccessSchedules",
    ]

    for field in policy_fields:
        if policy1.get(field) != policy2.get(field):
            return False

    for field in list_fields:
        if policy1.get(field, []) != policy2.get(field, []):
            return False

    return True


def compare_user_configs(config1: dict[str, Any], config2: dict[str, Any]) -> bool:
    config_fields = [
        "AudioLanguagePreference",
        "PlayDefaultAudioTrack",
        "SubtitleLanguagePreference",
        "DisplayMissingEpisodes",
        "GroupedFolders",
        "SubtitleMode",
        "DisplayCollectionsView",
        "EnableLocalPassword",
        "HidePlayedInLatest",
        "RememberAudioSelections",
        "RememberSubtitleSelections",
        "EnableNextEpisodeAutoPlay",
    ]

    list_fields = [
        "OrderedViews",
        "LatestItemsExcludes",
        "MyMediaExcludes",
    ]

    for field in config_fields:
        if config1.get(field) != config2.get(field):
            return False

    for field in list_fields:
        if config1.get(field, []) != config2.get(field, []):
            return False

    return True
