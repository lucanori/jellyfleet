
from jellyfleet.sync.server_comparisons import (
    compare_libraries,
    compare_server_configs,
)


def test_compare_libraries_identical():
    lib1 = {
        "Name": "Movies",
        "CollectionType": "movies",
        "LibraryOptions": {
            "EnableRealtimeMonitor": True,
            "EnableChapterImageExtraction": True,
        },
    }
    lib2 = {
        "Name": "Movies",
        "CollectionType": "movies",
        "LibraryOptions": {
            "EnableRealtimeMonitor": True,
            "EnableChapterImageExtraction": True,
        },
    }

    assert compare_libraries(lib1, lib2) is True


def test_compare_libraries_different_name():
    lib1 = {
        "Name": "Movies",
        "CollectionType": "movies",
        "LibraryOptions": {},
    }
    lib2 = {
        "Name": "TV Shows",
        "CollectionType": "movies",
        "LibraryOptions": {},
    }

    assert compare_libraries(lib1, lib2) is False


def test_compare_libraries_different_type():
    lib1 = {
        "Name": "Media",
        "CollectionType": "movies",
        "LibraryOptions": {},
    }
    lib2 = {
        "Name": "Media",
        "CollectionType": "tvshows",
        "LibraryOptions": {},
    }

    assert compare_libraries(lib1, lib2) is False


def test_compare_libraries_different_options():
    lib1 = {
        "Name": "Movies",
        "CollectionType": "movies",
        "LibraryOptions": {"EnableRealtimeMonitor": True},
    }
    lib2 = {
        "Name": "Movies",
        "CollectionType": "movies",
        "LibraryOptions": {"EnableRealtimeMonitor": False},
    }

    assert compare_libraries(lib1, lib2) is False


def test_compare_server_configs_identical():
    config1 = {
        "ServerName": "Jellyfin Server",
        "EnableUPnP": True,
        "PublicPort": 8096,
        "EnableHttps": False,
        "MetadataOptions": [{"Type": "Movie", "SaveLocalImages": True}],
        "RemoteIPFilter": [],
        "TrickplayImageInterval": 5,
    }
    config2 = {
        "ServerName": "Jellyfin Server",
        "EnableUPnP": True,
        "PublicPort": 8096,
        "EnableHttps": False,
        "MetadataOptions": [{"Type": "Movie", "SaveLocalImages": True}],
        "RemoteIPFilter": [],
        "TrickplayImageInterval": 5,
    }

    assert compare_server_configs(config1, config2) is True


def test_compare_server_configs_different():
    config1 = {
        "ServerName": "Jellyfin Server",
        "EnableUPnP": True,
        "PublicPort": 8096,
        "EnableHttps": False,
    }
    config2 = {
        "ServerName": "Jellyfin Server",
        "EnableUPnP": False,
        "PublicPort": 8096,
        "EnableHttps": False,
    }

    assert compare_server_configs(config1, config2) is False


def test_compare_server_configs_missing_fields():
    config1 = {
        "ServerName": "Jellyfin Server",
        "EnableUPnP": True,
        "PublicPort": 8096,
    }
    config2 = {
        "ServerName": "Jellyfin Server",
        "EnableUPnP": True,
        "PublicPort": 8096,
        "EnableHttps": False,
    }

    assert compare_server_configs(config1, config2) is False


def test_compare_server_configs_with_lists():
    config1 = {
        "ServerName": "Jellyfin Server",
        "EnableUPnP": True,
        "MetadataOptions": [{"Type": "Movie"}, {"Type": "Series"}],
        "RemoteIPFilter": ["192.168.1.0/24"],
    }
    config2 = {
        "ServerName": "Jellyfin Server",
        "EnableUPnP": True,
        "MetadataOptions": [{"Type": "Movie"}, {"Type": "Series"}],
        "RemoteIPFilter": ["192.168.1.0/24"],
    }

    assert compare_server_configs(config1, config2) is True


def test_compare_server_configs_different_lists():
    config1 = {
        "ServerName": "Jellyfin Server",
        "EnableUPnP": True,
        "MetadataOptions": [{"Type": "Movie"}],
        "RemoteIPFilter": ["192.168.1.0/24"],
    }
    config2 = {
        "ServerName": "Jellyfin Server",
        "EnableUPnP": True,
        "MetadataOptions": [{"Type": "Movie"}, {"Type": "Series"}],
        "RemoteIPFilter": ["192.168.1.0/24"],
    }

    assert compare_server_configs(config1, config2) is False


def test_compare_server_configs_trickplay_fields():
    config1 = {
        "ServerName": "Jellyfin Server",
        "TrickplayImageInterval": 5,
        "TrickplayImageMaxAge": "30.00:00:00",
        "TrickplayImageMaxAgeDays": 30,
    }
    config2 = {
        "ServerName": "Jellyfin Server",
        "TrickplayImageInterval": 5,
        "TrickplayImageMaxAge": "30.00:00:00",
        "TrickplayImageMaxAgeDays": 30,
    }

    assert compare_server_configs(config1, config2) is True
