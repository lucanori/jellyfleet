from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from jellyfleet.config.models import AppConfig


def load_raw_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    content = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as error:
        message = "Invalid YAML"
        raise ValueError(message) from error
    if not isinstance(data, dict):
        message = "Configuration must be a mapping"
        raise TypeError(message)
    return data


async def load_config(path: str) -> AppConfig:
    file_path = Path(path)
    data = load_raw_yaml(file_path)
    try:
        return AppConfig.model_validate(data)
    except ValidationError as error:
        raise error from None
