from dataclasses import dataclass


@dataclass
class Logger:
    level: str = "INFO"
