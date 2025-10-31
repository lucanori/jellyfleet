from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from jellyfleet.db.models import SyncRun


class SyncRepository:
    def __init__(self, session) -> None:
        self.session = session

    def create_sync_run(
        self,
        combination_name: str,
        father_server: str,
        child_server: str,
        domains: list[str],
        dry_run: bool = False,
    ) -> SyncRun:
        sync_run = SyncRun(
            combination_name=combination_name,
            father_server=father_server,
            child_server=child_server,
            domains=",".join(domains),
            dry_run=dry_run,
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(sync_run)
        self.session.commit()
        self.session.refresh(sync_run)
        return sync_run

    def complete_sync_run(
        self,
        sync_run_id: int,
        status: str,
        actions_count: int = 0,
        error_message: str | None = None,
        details: str | None = None,
    ) -> SyncRun:
        sync_run = self.session.get(SyncRun, sync_run_id)
        if sync_run is None:
            message = f"Sync run {sync_run_id} not found"
            raise ValueError(message)
        sync_run.status = status
        sync_run.completed_at = datetime.now(timezone.utc)
        sync_run.actions_count = actions_count
        sync_run.error_message = error_message
        sync_run.details = details
        self.session.commit()
        self.session.refresh(sync_run)
        return sync_run

    def get_recent_sync_runs(
        self, combination_name: str | None = None, limit: int = 50
    ) -> list[SyncRun]:
        query = select(SyncRun).order_by(SyncRun.started_at.desc())
        if combination_name:
            query = query.where(SyncRun.combination_name == combination_name)
        query = query.limit(limit)
        return list(self.session.execute(query).scalars().all())

    def get_sync_runs_for_pair(
        self, father_server: str, child_server: str, limit: int = 3
    ) -> list[SyncRun]:
        query = (
            select(SyncRun)
            .where(SyncRun.father_server == father_server)
            .where(SyncRun.child_server == child_server)
            .order_by(SyncRun.started_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(query).scalars().all())

    def apply_retention_policy(self, keep_per_pair: int = 3) -> int:
        pairs_query = (
            select(SyncRun.father_server, SyncRun.child_server)
            .distinct()
            .order_by(SyncRun.father_server, SyncRun.child_server)
        )
        pairs = self.session.execute(pairs_query).all()

        total_deleted = 0
        for father_server, child_server in pairs:
            query = (
                select(SyncRun)
                .where(SyncRun.father_server == father_server)
                .where(SyncRun.child_server == child_server)
                .order_by(SyncRun.started_at.desc())
            )
            all_runs = list(self.session.execute(query).scalars().all())

            if len(all_runs) > keep_per_pair:
                runs_to_delete = all_runs[keep_per_pair:]
                for run in runs_to_delete:
                    self.session.delete(run)
                    total_deleted += 1

        if total_deleted > 0:
            self.session.commit()
        return total_deleted

    def get_sync_run(self, sync_run_id: int) -> SyncRun | None:
        return self.session.get(SyncRun, sync_run_id)
