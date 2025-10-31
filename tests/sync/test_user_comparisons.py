from jellyfleet.sync.user_comparisons import (
    compare_user_configs,
    compare_user_policies,
    compare_users,
)


def test_compare_users_identical():
    user1 = {
        "Name": "testuser",
        "HasPassword": True,
        "HasConfiguredPassword": True,
        "EnableAutoLogin": False,
        "LastLoginDate": "2023-01-01T00:00:00Z",
        "LastActivityDate": "2023-01-01T01:00:00Z",
    }
    user2 = {
        "Name": "testuser",
        "HasPassword": True,
        "HasConfiguredPassword": True,
        "EnableAutoLogin": False,
        "LastLoginDate": "2023-01-01T00:00:00Z",
        "LastActivityDate": "2023-01-01T01:00:00Z",
    }

    assert compare_users(user1, user2) is True


def test_compare_users_different():
    user1 = {
        "Name": "testuser",
        "HasPassword": True,
        "HasConfiguredPassword": True,
        "EnableAutoLogin": False,
        "LastLoginDate": "2023-01-01T00:00:00Z",
        "LastActivityDate": "2023-01-01T01:00:00Z",
    }
    user2 = {
        "Name": "testuser",
        "HasPassword": False,
        "HasConfiguredPassword": True,
        "EnableAutoLogin": False,
        "LastLoginDate": "2023-01-01T00:00:00Z",
        "LastActivityDate": "2023-01-01T01:00:00Z",
    }

    assert compare_users(user1, user2) is False


def test_compare_user_policies_identical():
    policy1 = {
        "IsAdministrator": False,
        "IsHidden": False,
        "IsDisabled": False,
        "EnableContentDeletion": False,
        "EnabledFolders": ["movies", "tv"],
        "BlockedTags": ["horror"],
    }
    policy2 = {
        "IsAdministrator": False,
        "IsHidden": False,
        "IsDisabled": False,
        "EnableContentDeletion": False,
        "EnabledFolders": ["movies", "tv"],
        "BlockedTags": ["horror"],
    }

    assert compare_user_policies(policy1, policy2) is True


def test_compare_user_policies_different():
    policy1 = {
        "IsAdministrator": False,
        "IsHidden": False,
        "IsDisabled": False,
        "EnableContentDeletion": False,
        "EnabledFolders": ["movies", "tv"],
        "BlockedTags": ["horror"],
    }
    policy2 = {
        "IsAdministrator": True,
        "IsHidden": False,
        "IsDisabled": False,
        "EnableContentDeletion": False,
        "EnabledFolders": ["movies", "tv"],
        "BlockedTags": ["horror"],
    }

    assert compare_user_policies(policy1, policy2) is False


def test_compare_user_policies_different_lists():
    policy1 = {
        "IsAdministrator": False,
        "EnabledFolders": ["movies", "tv"],
        "BlockedTags": ["horror"],
    }
    policy2 = {
        "IsAdministrator": False,
        "EnabledFolders": ["movies"],
        "BlockedTags": ["horror"],
    }

    assert compare_user_policies(policy1, policy2) is False


def test_compare_user_configs_identical():
    config1 = {
        "AudioLanguagePreference": "en",
        "PlayDefaultAudioTrack": True,
        "SubtitleLanguagePreference": "en",
        "DisplayMissingEpisodes": True,
        "GroupedFolders": [],
        "SubtitleMode": "Default",
        "DisplayCollectionsView": False,
        "EnableLocalPassword": False,
        "OrderedViews": ["movies", "tv"],
        "LatestItemsExcludes": [],
        "MyMediaExcludes": [],
        "HidePlayedInLatest": False,
        "RememberAudioSelections": True,
        "RememberSubtitleSelections": True,
        "EnableNextEpisodeAutoPlay": True,
    }
    config2 = {
        "AudioLanguagePreference": "en",
        "PlayDefaultAudioTrack": True,
        "SubtitleLanguagePreference": "en",
        "DisplayMissingEpisodes": True,
        "GroupedFolders": [],
        "SubtitleMode": "Default",
        "DisplayCollectionsView": False,
        "EnableLocalPassword": False,
        "OrderedViews": ["movies", "tv"],
        "LatestItemsExcludes": [],
        "MyMediaExcludes": [],
        "HidePlayedInLatest": False,
        "RememberAudioSelections": True,
        "RememberSubtitleSelections": True,
        "EnableNextEpisodeAutoPlay": True,
    }

    assert compare_user_configs(config1, config2) is True


def test_compare_user_configs_different():
    config1 = {
        "AudioLanguagePreference": "en",
        "PlayDefaultAudioTrack": True,
        "SubtitleLanguagePreference": "en",
    }
    config2 = {
        "AudioLanguagePreference": "fr",
        "PlayDefaultAudioTrack": True,
        "SubtitleLanguagePreference": "en",
    }

    assert compare_user_configs(config1, config2) is False


def test_compare_user_configs_missing_lists():
    config1 = {
        "AudioLanguagePreference": "en",
        "PlayDefaultAudioTrack": True,
        "SubtitleLanguagePreference": "en",
    }
    config2 = {
        "AudioLanguagePreference": "en",
        "PlayDefaultAudioTrack": True,
        "SubtitleLanguagePreference": "en",
        "OrderedViews": ["movies", "tv"],
    }

    assert compare_user_configs(config1, config2) is False
