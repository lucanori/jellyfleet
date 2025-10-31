import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from jellyfleet.config.utils import (
    ensure_secrets_directory,
    get_config_from_env,
    get_default_config_path,
    get_secrets_directory,
    merge_config_with_env,
    validate_config_file_path,
)


def test_get_default_config_path():
    result = get_default_config_path()
    assert result == Path.cwd() / "config.yaml"


def test_get_config_from_env_empty():
    with patch.dict(os.environ, {}, clear=True):
        result = get_config_from_env()
        assert result == {}


def test_get_config_from_env_with_values():
    env_vars = {
        "JELLYFLEET_DB_PATH": "/custom/db.sqlite",
        "JELLYFLEET_LOG_LEVEL": "DEBUG",
        "JELLYFLEET_DRY_RUN": "true",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        result = get_config_from_env()

        assert result == {
            "runtime": {
                "db_path": "/custom/db.sqlite",
                "log_level": "DEBUG",
                "dry_run": True,
            }
        }


def test_get_config_from_env_dry_run_false():
    env_vars = {"JELLYFLEET_DRY_RUN": "false"}

    with patch.dict(os.environ, env_vars, clear=True):
        result = get_config_from_env()

        assert result == {"runtime": {"dry_run": False}}


def test_get_secrets_directory_default():
    with patch.dict(os.environ, {}, clear=True):
        result = get_secrets_directory()
        assert result == Path.cwd() / "secrets"


def test_get_secrets_directory_from_env():
    with patch.dict(os.environ, {"JELLYFLEET_SECRETS_DIR": "/custom/secrets"}):
        result = get_secrets_directory()
        assert result == Path("/custom/secrets")


def test_ensure_secrets_directory_creates_directory():
    with tempfile.TemporaryDirectory() as temp_dir:
        secrets_dir = Path(temp_dir) / "new_secrets"

        with patch.dict(os.environ, {"JELLYFLEET_SECRETS_DIR": str(secrets_dir)}):
            result = ensure_secrets_directory()

            assert result == secrets_dir
            assert secrets_dir.exists()
            assert secrets_dir.is_dir()


def test_ensure_secrets_directory_existing():
    with tempfile.TemporaryDirectory() as temp_dir:
        secrets_dir = Path(temp_dir) / "existing_secrets"
        secrets_dir.mkdir()

        with patch.dict(os.environ, {"JELLYFLEET_SECRETS_DIR": str(secrets_dir)}):
            result = ensure_secrets_directory()

            assert result == secrets_dir
            assert secrets_dir.exists()


def test_validate_config_file_path_success():
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        result = validate_config_file_path(temp_path)
        assert result == temp_path.resolve()
    finally:
        temp_path.unlink()


def test_validate_config_file_path_not_found():
    non_existent = Path("/non/existent/config.yaml")

    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        validate_config_file_path(non_existent)


def test_validate_config_file_path_not_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = Path(temp_dir)

        with pytest.raises(ValueError, match="Configuration path is not a file"):
            validate_config_file_path(dir_path)


def test_validate_config_file_path_wrong_extension():
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        with pytest.raises(ValueError, match="Configuration file must be YAML"):
            validate_config_file_path(temp_path)
    finally:
        temp_path.unlink()


def test_merge_config_with_env_empty_overrides():
    from jellyfleet.config.models import (
        AppConfig,
        ChildConfig,
        CombinationConfig,
        Domain,
        ServerConfig,
    )

    config = AppConfig(
        servers={"test_server": ServerConfig(url="http://test", token="test")},
        combinations=[
            CombinationConfig(
                name="test",
                father="test_server",
                children=[
                    ChildConfig(
                        server="test_server",
                        domains=[Domain.users],
                    )
                ],
            )
        ],
    )

    result = merge_config_with_env(config, {})
    assert result == config


def test_merge_config_with_env_simple_override():
    from jellyfleet.config.models import (
        AppConfig,
        ChildConfig,
        CombinationConfig,
        Domain,
        ServerConfig,
    )

    config = AppConfig(
        servers={"test_server": ServerConfig(url="http://test", token="test")},
        combinations=[
            CombinationConfig(
                name="test",
                father="test_server",
                children=[
                    ChildConfig(
                        server="test_server",
                        domains=[Domain.users],
                    )
                ],
            )
        ],
        runtime={"dry_run": False},
    )

    overrides = {"runtime": {"dry_run": True}}
    result = merge_config_with_env(config, overrides)

    assert result.runtime.dry_run is True


def test_merge_config_with_env_nested_override():
    from jellyfleet.config.models import (
        AppConfig,
        ChildConfig,
        CombinationConfig,
        Domain,
        ServerConfig,
    )

    config = AppConfig(
        servers={"test": ServerConfig(url="http://old", token="old")},
        combinations=[
            CombinationConfig(
                name="test",
                father="test",
                children=[
                    ChildConfig(
                        server="test",
                        domains=[Domain.users],
                    )
                ],
            )
        ],
    )

    overrides = {"servers": {"test": {"url": "http://new"}}}
    result = merge_config_with_env(config, overrides)

    assert str(result.servers["test"].url) == "http://new/"
    assert result.servers["test"].token.get_secret_value() == "old"
