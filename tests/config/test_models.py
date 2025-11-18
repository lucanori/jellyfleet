import pytest
from pydantic import ValidationError

from jellyfleet.config.models import AppConfig, ChildConfig, SecretRef


def test_secret_ref_requires_single_source():
    with pytest.raises(ValidationError):
        SecretRef(value="one", env="TOKEN")


def test_child_domains_must_be_valid():
    with pytest.raises(ValidationError):
        ChildConfig(server="child-a", domains=["users", "invalid"])


def test_combination_requires_existing_servers():
    data = {
        "servers": {
            "father-a": {
                "url": "https://father",
                "token": {"value": "token"},
            }
        },
        "combinations": [
            {
                "name": "sync-a",
                "father": "father-a",
                "children": [
                    {
                        "server": "unknown-child",
                        "domains": ["users"],
                    }
                ],
            }
        ],
    }
    with pytest.raises(ValidationError):
        AppConfig.model_validate(data)
