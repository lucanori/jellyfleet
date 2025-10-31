from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from jellyfleet.config.models import AppConfig


def get_default_config_path() -> Path:
    return Path.cwd() / "config.yaml"


def get_config_from_env() -> dict[str, Any]:
    config_overrides = {}

    db_path = os.getenv("JELLYFLEET_DB_PATH")
    if db_path:
        config_overrides.setdefault("runtime", {})["db_path"] = db_path

    log_level = os.getenv("JELLYFLEET_LOG_LEVEL")
    if log_level:
        config_overrides.setdefault("runtime", {})["log_level"] = log_level

    dry_run = os.getenv("JELLYFLEET_DRY_RUN")
    if dry_run is not None:
        config_overrides.setdefault("runtime", {})["dry_run"] = dry_run.lower() in (
            "true",
            "1",
            "yes",
        )

    return config_overrides


def merge_config_with_env(
    config: AppConfig, env_overrides: dict[str, Any]
) -> AppConfig:
    if not env_overrides:
        return config

    config_dict = config.model_dump()

    def deep_merge(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
        for key, value in overrides.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    merged_dict = deep_merge(config_dict, env_overrides)
    return AppConfig.model_validate(merged_dict)


def validate_config_file_path(path: str | Path) -> Path:
    config_path = Path(path)

    if not config_path.exists():
        message = f"Configuration file not found: {config_path}"
        raise FileNotFoundError(message)

    if not config_path.is_file():
        message = f"Configuration path is not a file: {config_path}"
        raise ValueError(message)

    if config_path.suffix not in (".yaml", ".yml"):
        message = f"Configuration file must be YAML (.yaml or .yml): {config_path}"
        raise ValueError(message)

    return config_path.resolve()


def get_secrets_directory() -> Path:
    secrets_dir = os.getenv("JELLYFLEET_SECRETS_DIR")
    if secrets_dir:
        return Path(secrets_dir).expanduser().resolve()

    return Path.cwd() / "secrets"


def ensure_secrets_directory() -> Path:
    secrets_dir = get_secrets_directory()
    secrets_dir.mkdir(parents=True, exist_ok=True)
    return secrets_dir
