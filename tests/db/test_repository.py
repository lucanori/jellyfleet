import pytest

from jellyfleet.db.base import create_database_engine, create_session_factory
from jellyfleet.db.models import SyncRun
from jellyfleet.db.repository import SyncRepository

EXPECTED_ACTIONS_COUNT = 5
EXPECTED_CHILDREN_COUNT = 2
EXPECTED_TOTAL_DOMAINS = 4
EXPECTED_MODIFIED_DOMAINS = 3
EXPECTED_LIBRARY_COUNT = 2
EXPECTED_REMAINING_COUNT = 2


@pytest.fixture
def in_memory_db():
    engine = create_database_engine(":memory:")
    SyncRun.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def repository(in_memory_db):
    return SyncRepository(in_memory_db)


def test_create_sync_run(repository):
    sync_run = repository.create_sync_run(
        combination_name="test-combo",
        father_server="father",
        child_server="child",
        domains=["users", "libraries"],
        dry_run=False,
    )

    assert sync_run.id is not None
    assert sync_run.combination_name == "test-combo"
    assert sync_run.father_server == "father"
    assert sync_run.child_server == "child"
    assert sync_run.domains == "users,libraries"
    assert sync_run.dry_run is False
    assert sync_run.status == "running"
    assert sync_run.started_at is not None
    assert sync_run.completed_at is None
    assert sync_run.actions_count == 0


def test_complete_sync_run_success(repository):
    sync_run = repository.create_sync_run(
        combination_name="test-combo",
        father_server="father",
        child_server="child",
        domains=["users"],
    )

    completed = repository.complete_sync_run(
        sync_run.id,
        status="completed",
        actions_count=EXPECTED_ACTIONS_COUNT,
        details="Sync completed successfully",
    )

    assert completed.id == sync_run.id
    assert completed.status == "completed"
    assert completed.completed_at is not None
    assert completed.actions_count == EXPECTED_ACTIONS_COUNT
    assert completed.details == "Sync completed successfully"
    assert completed.error_message is None


def test_complete_sync_run_with_error(repository):
    sync_run = repository.create_sync_run(
        combination_name="test-combo",
        father_server="father",
        child_server="child",
        domains=["users"],
    )

    completed = repository.complete_sync_run(
        sync_run.id,
        status="failed",
        error_message="Connection timeout",
    )

    assert completed.status == "failed"
    assert completed.error_message == "Connection timeout"
    assert completed.completed_at is not None


def test_complete_sync_run_not_found(repository):
    with pytest.raises(ValueError, match="Sync run 999 not found"):
        repository.complete_sync_run(999, "completed")


def test_get_recent_sync_runs(repository):
    repository.create_sync_run("combo1", "father1", "child1", ["users"])
    repository.create_sync_run("combo2", "father2", "child2", ["libraries"])

    recent = repository.get_recent_sync_runs()
    assert len(recent) == EXPECTED_CHILDREN_COUNT
    assert recent[0].combination_name == "combo2"
    assert recent[1].combination_name == "combo1"


def test_get_recent_sync_runs_by_combination(repository):
    repository.create_sync_run("combo1", "father1", "child1", ["users"])
    repository.create_sync_run("combo2", "father2", "child2", ["libraries"])
    repository.create_sync_run("combo1", "father1", "child1", ["settings"])

    combo1_runs = repository.get_recent_sync_runs(combination_name="combo1")
    assert len(combo1_runs) == EXPECTED_CHILDREN_COUNT
    assert all(run.combination_name == "combo1" for run in combo1_runs)


def test_get_sync_runs_for_pair(repository):
    repository.create_sync_run("combo1", "father1", "child1", ["users"])
    repository.create_sync_run("combo2", "father1", "child1", ["libraries"])
    repository.create_sync_run("combo3", "father1", "child2", ["users"])

    pair_runs = repository.get_sync_runs_for_pair("father1", "child1")
    assert len(pair_runs) == EXPECTED_CHILDREN_COUNT
    assert all(
        run.father_server == "father1" and run.child_server == "child1"
        for run in pair_runs
    )


def test_apply_retention_policy(repository):
    for i in range(5):
        repository.create_sync_run(f"combo{i}", "father", "child", ["users"])

    deleted_count = repository.apply_retention_policy(
        keep_per_pair=EXPECTED_MODIFIED_DOMAINS
    )
    assert deleted_count == EXPECTED_CHILDREN_COUNT

    remaining_runs = repository.get_sync_runs_for_pair("father", "child")
    assert len(remaining_runs) == EXPECTED_MODIFIED_DOMAINS


def test_apply_retention_policy_multiple_pairs(repository):
    for i in range(4):
        repository.create_sync_run(f"combo{i}", "father1", "child1", ["users"])
        repository.create_sync_run(f"combo{i}", "father2", "child2", ["users"])

    deleted_count = repository.apply_retention_policy(
        keep_per_pair=EXPECTED_CHILDREN_COUNT
    )
    assert deleted_count == EXPECTED_TOTAL_DOMAINS

    remaining_pair1 = repository.get_sync_runs_for_pair("father1", "child1")
    remaining_pair2 = repository.get_sync_runs_for_pair("father2", "child2")
    assert len(remaining_pair1) == EXPECTED_REMAINING_COUNT
    assert len(remaining_pair2) == EXPECTED_REMAINING_COUNT


def test_get_sync_run(repository):
    created = repository.create_sync_run("combo", "father", "child", ["users"])
    retrieved = repository.get_sync_run(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.combination_name == "combo"


def test_get_sync_run_not_found(repository):
    result = repository.get_sync_run(999)
    assert result is None
