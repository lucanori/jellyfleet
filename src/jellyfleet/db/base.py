from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

Base = declarative_base()


def create_database_engine(database_path: str):
    return create_engine(f"sqlite:///{database_path}")


def create_session_factory(engine):
    return sessionmaker(bind=engine)


@asynccontextmanager
async def get_session() -> AsyncGenerator[sessionmaker, None]:
    engine = create_database_engine("jellyfleet.db")
    session_factory = create_session_factory(engine)

    try:
        yield session_factory
    finally:
        engine.dispose()
