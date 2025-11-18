from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from jellyfleet.db.base import Base


class SyncRun(Base):
    __tablename__ = "sync_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    combination_name: Mapped[str] = mapped_column(String(255), nullable=False)
    father_server: Mapped[str] = mapped_column(String(255), nullable=False)
    child_server: Mapped[str] = mapped_column(String(255), nullable=False)
    domains: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    dry_run: Mapped[bool] = mapped_column(default=False)
    actions_count: Mapped[int] = mapped_column(Integer, default=0)
    details: Mapped[str] = mapped_column(Text, nullable=True)
