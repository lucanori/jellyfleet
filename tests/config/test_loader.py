import pytest
from pydantic import ValidationError

from jellyfleet.config.loader import load_config


@pytest.mark.asyncio
async def test_load_config_reads_yaml(tmp_path, monkeypatch):
    file = tmp_path / "config.yaml"
    file.write_text(
        """
servers:
  father:
    url: https://father
    token:
      value: secret
  child:
    url: https://child
    token:
      value: child-secret
combinations:
  - name: combo
    father: father
    children:
      - server: child
        domains: [users]
"""
    )
    monkeypatch.chdir(tmp_path)
    config = await load_config("config.yaml")
    assert str(config.servers["father"].url) == "https://father/"


@pytest.mark.asyncio
async def test_load_config_expands_environment(tmp_path, monkeypatch):
    file = tmp_path / "config.yaml"
    file.write_text(
        """
servers:
  father:
    url: https://father
    token:
      env: TOKEN
  child:
    url: https://child
    token:
      value: child-secret
combinations:
  - name: combo
    father: father
    children:
      - server: child
        domains: [users]
"""
    )
    monkeypatch.setenv("TOKEN", "abc123")
    monkeypatch.chdir(tmp_path)
    config = await load_config("config.yaml")
    assert config.servers["father"].token.get_secret_value() == "abc123"


@pytest.mark.asyncio
async def test_load_config_raises_on_invalid_file(tmp_path, monkeypatch):
    file = tmp_path / "config.yaml"
    file.write_text("invalid:")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValidationError):
        await load_config("config.yaml")
