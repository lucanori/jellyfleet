from __future__ import annotations

import os
from enum import Enum
from pathlib import Path

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    SecretStr,
    ValidationInfo,
    field_validator,
    model_validator,
)


class SecretRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str | None = None
    env: str | None = None
    file: str | None = None

    @model_validator(mode="after")
    def check_single_source(self) -> SecretRef:
        sources = [
            source
            for source in (self.value, self.env, self.file)
            if source not in (None, "")
        ]
        if len(sources) != 1:
            message = "Provide exactly one secret source"
            raise ValueError(message)
        return self

    def resolve(self, base_path: Path | None = None) -> str:
        if self.value not in (None, ""):
            return self.value  # type: ignore[return-value]
        if self.env not in (None, ""):
            resolved = os.getenv(self.env)  # type: ignore[arg-type]
            if resolved is None:
                message = f"Environment variable {self.env} is not set"
                raise ValueError(message)
            return resolved
        if self.file not in (None, ""):
            base = Path(base_path or Path.cwd())
            target = (base / self.file).expanduser()  # type: ignore[arg-type]
            if not target.is_file():
                raise FileNotFoundError(target)
            return target.read_text(encoding="utf-8").strip()
        message = "Secret reference is not defined"
        raise ValueError(message)


class Domain(str, Enum):
    users = "users"
    libraries = "libraries"
    settings = "settings"


class ChildConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    server: str
    domains: list[Domain] = Field(min_length=1)

    @field_validator("domains")
    @classmethod
    def ensure_unique_domains(cls, value: list[Domain]) -> list[Domain]:
        seen = []
        for domain in value:
            if domain not in seen:
                seen.append(domain)
        return seen


class CombinationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    father: str
    children: list[ChildConfig] = Field(min_length=1)
    dry_run: bool | None = None


class SchedulerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cron: str = "0 */6 * * *"
    timezone: str | None = None


class RuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dry_run: bool = False


class ServerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: HttpUrl
    token: SecretStr

    @field_validator("token", mode="before")
    @classmethod
    def convert_token(cls, value: object, info: ValidationInfo) -> SecretStr:
        if isinstance(value, SecretStr):
            return value
        if isinstance(value, str):
            return SecretStr(value)
        if isinstance(value, dict):
            ref = SecretRef.model_validate(value)
            base_path: Path | None = None
            if info.context and "base_path" in info.context:
                context_path = info.context["base_path"]
                if context_path is not None:
                    base_path = Path(context_path)
            return SecretStr(ref.resolve(base_path))
        message = "Invalid token definition"
        raise TypeError(message)


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    servers: dict[str, ServerConfig]
    combinations: list[CombinationConfig] = Field(min_length=1)
    scheduler: SchedulerConfig = SchedulerConfig()
    runtime: RuntimeConfig = RuntimeConfig()

    @model_validator(mode="after")
    def validate_relationships(self) -> AppConfig:
        server_names = set(self.servers.keys())
        for combination in self.combinations:
            if combination.father not in server_names:
                message = f"Father server '{combination.father}' is not defined"
                raise ValueError(message)
            for child in combination.children:
                if child.server not in server_names:
                    message = f"Child server '{child.server}' is not defined"
                    raise ValueError(message)
        return self
