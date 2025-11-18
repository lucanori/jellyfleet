import jellyfleet
from jellyfleet.cli import cli
from jellyfleet.config import Config
from jellyfleet.db import Database
from jellyfleet.jellyfin import JellyfinClient
from jellyfleet.logging import Logger
from jellyfleet.scheduler import Scheduler
from jellyfleet.sync import SyncOrchestrator


def test_jellyfleet_import():
    assert jellyfleet is not None


def test_config_import():
    assert Config is not None


def test_jellyfin_import():
    assert JellyfinClient is not None


def test_sync_import():
    assert SyncOrchestrator is not None


def test_db_import():
    assert Database is not None


def test_scheduler_import():
    assert Scheduler is not None


def test_cli_import():
    assert cli is not None


def test_logging_import():
    assert Logger is not None
