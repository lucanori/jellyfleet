# Jellyfleet Synchronization Service Implementation Plan

## Overview

Jellyfleet is a configuration-driven synchronization service that propagates users, libraries, and primary settings across two or more Jellyfin instances arranged in father→child relationships. Every synchronization run is scheduled (no real-time transport) and lets each child choose which data domains (users, libraries, settings) to import from its assigned father. The service provides dry-run capabilities, structured logging, and flexible secret handling (inline values, environment variables, or secrets files). Implementation will be in Python using uv, delivered as a single scheduled container via Docker (with docker-bake), and developed strictly with TDD per repository guidelines.

## Current State Analysis

- Repository currently contains CI workflows, docker-bake configuration, LICENSE, semantic-release setup, and a Jellyfin API research document.
- No application source code, configuration samples, Dockerfile, or tests exist yet.
- docker-bake assumes a Dockerfile that is not present; no docker-compose stack is defined.
- `.github/CONTRIBUTING.md` mandates: no inline code comments, Conventional Commits, TDD with ≥85% coverage, `uv` for dependencies, `pytest` for tests, `ruff` for lint/format, and file length caps (≤500 lines for source, ≤600 for tests).

## Desired End State

A production-ready synchronization service with:

- Python project rooted under `src/jellyfleet`, developed with TDD and ≥85% coverage, packaged with uv.
- CLI entrypoint enabling scheduled runs, configurable cron expressions (default 6 hours) with guidance to avoid intervals shorter than 5 minutes.
- YAML configuration file that defines multiple father/child combinations and per-child domain selections. Secrets can be provided inline, via environment substitution, or by referencing external secret files.
- Token-based authentication to Jellyfin instances using user-provided tokens; no runtime credential issuance. Multiple credential sourcing strategies supported via config.
- Sync engine capable of dry-run (diff-only) and apply modes, producing structured INFO logs (concise) and detailed DEBUG logs with per-action traces.
- SQLite persistence layer managing schema migrations plus rolling history (last three sync runs per father-child combination) with status metadata.
- Dockerfile aligned with docker-bake for multi-arch builds and docker-compose sample for deployment.
- Documentation covering configuration schema, scheduling guidance, dry-run usage, logging profiles, and operational best practices.

### Key Discoveries
- Jellyfin REST API supports user management (`UserController`), configuration (`ConfigurationController`, `DisplayPreferencesController`), library operations, and backups.
- Authentication uses token headers (`Authorization: MediaBrowser Token="…"`). Tokens must be created manually per instance.
- Repository standards prohibit code comments, enforce small file sizes, and require strict lint/test checks via `ruff` and `pytest`.
- docker-bake is preconfigured for multi-architecture builds and expects descriptive labels but currently references a missing Dockerfile.

### What We're NOT Doing
- No real-time synchronization or WebSocket listeners.
- No UI/dashboard; operation remains CLI/cron-based.
- No additional CI workflow authoring (existing GitHub Actions remain).
- No automated credential management (users supply tokens).
- No filesystem/media synchronization beyond Jellyfin API operations.

## Implementation Approach

Develop the service in incremental phases, each led by failing tests. Modules will be separated by concern: configuration management, Jellyfin clients, domain-specific sync logic, persistence, scheduling/CLI orchestration, and observability. Each phase concludes with automated and manual success checks.

## Phase 1: Project Scaffolding & Tooling

### Overview
Create Python project structure, dependency metadata, testing/linting pipeline, foundational Docker artifacts, and baseline documentation.

### Changes Required

#### 1. Project Structure & Tooling
**File**: `pyproject.toml`
**Changes**: Define project metadata, uv configuration, runtime dependencies (`httpx`, `pydantic`, `sqlalchemy`/`alembic`, `croniter`, `structlog`, `python-dotenv`), and dev dependencies (`pytest`, `pytest-cov`, `ruff`, `pytest-httpx` or `responses`). Configure `pytest` and `ruff` settings.
- [x] Implemented 2025-10-31

**File**: `uv.lock`
**Changes**: Generate lockfile via `uv pip compile` or `uv sync`.
- [x] Implemented 2025-10-31

**Directory**: `src/jellyfleet/`
**Changes**: Initialize package (`__init__.py`), create placeholder modules (`config`, `jellyfin`, `sync`, `db`, `scheduler`, `cli`, `logging`).
- [x] Implemented 2025-10-31

**Directory**: `tests/`
**Changes**: Set up pytest structure with initial sanity test ensuring harness runs.
- [x] Implemented 2025-10-31

#### 2. Container & Tooling Assets
**File**: `Dockerfile`
**Changes**: Single-stage build using Python base, installing uv, copying project, running `uv sync`, setting non-root user, and defining entrypoint. Adjust docker-bake labels if needed.
- [x] Implemented 2025-10-31

**File**: `.dockerignore`
**Changes**: Exclude virtualenvs, caches, build artifacts.
- [x] Implemented 2025-10-31

**File**: `.env.example`
**Changes**: Document environment variables (database path, log level, secret references).
- [x] Implemented 2025-10-31

**File**: `README.md`
**Changes**: Add project description, development setup steps (`uv sync`, tests, lint), and quickstart.
- [x] Implemented 2025-10-31

**Optional**: `Makefile` or equivalent helper script for repetitive tasks (`make test`, `make lint`, `make format`, `make docker-build`).
- [x] Implemented 2025-10-31

### Success Criteria

#### Automated Verification
- [x] `uv run pytest` passes (placeholder tests).
- [x] `uv run ruff check .` and `uv run ruff format --check .` succeed.
- [x] `docker build -t jellyfleet:dev .` completes using new Dockerfile.

#### Manual Verification
- [x] `uv sync` installs dependencies without errors.
- [x] Running the container prints placeholder CLI help.
- [x] README instructions reproduce local setup.

---

## Phase 2: Configuration System

### Overview
Implement YAML-based configuration loader with schema enforcement, environment and secrets support, and documentation.

### Changes Required

#### 1. Configuration Models
**File**: `src/jellyfleet/config/models.py`
**Changes**: Define Pydantic models for servers, combinations, domain selections, secret references, scheduler defaults, and runtime flags (dry-run). Include validation ensuring referenced servers exist and domain values are constrained to {users, libraries, settings}.

#### 2. Loader & Utilities
**File**: `src/jellyfleet/config/loader.py`
**Changes**: Implement functions to load YAML, resolve `${ENV}` placeholders, read secret files, and hydrate models. Provide CLI-friendly error messages.

#### 3. Schema Documentation
**File**: `docs/configuration.md`
**Changes**: Document YAML schema, secrets handling (inline/env/secret file), multi-father/child examples, dry-run and scheduler configuration.

#### 4. Tests
**Files**: `tests/config/test_loader.py`, `tests/config/test_models.py`
**Changes**: TDD for valid config parsing, error cases, environment substitution, secret file reading, domain selection validation, scheduler defaults.

### Success Criteria

#### Automated Verification
- [x] `uv run pytest tests/config` passes. (2025-10-31)
- [x] Coverage ≥85% maintained. (2025-10-31)
- [x] `uv run ruff check src/jellyfleet/config` passes. (2025-10-31)

#### Manual Verification
- [x] `uv run jellyfleet config validate config/example.yaml` reports success. (2025-10-31)
- [x] Invalid configs produce helpful error messages. (2025-10-31)

---

## Phase 3: Jellyfin Client Layer

### Overview
Create HTTP client abstractions to communicate with Jellyfin REST endpoints for users, settings, and libraries, including authentication, retries, and structured logging.

### Changes Required

#### 1. Base Client Infrastructure
**File**: `src/jellyfleet/jellyfin/client.py`
**Changes**: Implement base class wrapping `httpx`, injecting token header, handling retries/backoff, logging request/response metadata (DEBUG level), and raising custom exceptions.

#### 2. Domain Clients
**Files**:
- `src/jellyfleet/jellyfin/users.py`: CRUD operations, policy/config updates.
- `src/jellyfleet/jellyfin/settings.py`: Server configuration, user configuration, display preferences access.
- `src/jellyfleet/jellyfin/libraries.py`: Library enumeration and modifications.

#### 3. Exceptions & Utilities
**File**: `src/jellyfleet/jellyfin/exceptions.py`
**Changes**: Define authentication, rate-limit, and validation exceptions.

#### 4. Tests
**Files**: `tests/jellyfleet/test_client.py`, `tests/jellyfleet/test_users.py`, `tests/jellyfleet/test_settings.py`, `tests/jellyfleet/test_libraries.py`
**Changes**: Use HTTP mocking (pytest-httpx/responses) to verify headers, retry logic, endpoint usage, payload shapes, error propagation.

### Success Criteria

#### Automated Verification
- [ ] `uv run pytest tests/jellyfleet` passes.
- [ ] Coverage ≥85% maintained.
- [ ] Lint passes for client modules.

#### Manual Verification
- [ ] CLI command `uv run jellyfleet client ping --config config/example.yaml` (or equivalent) handles reachable/unreachable instances gracefully, logging appropriately.

---

## Phase 4: SQLite Persistence & Sync History

### Overview
Introduce SQLite database with migrations to track sync runs, statuses, and retention of last three runs per father-child pair.

### Changes Required

#### 1. Database Schema & Migrations
**Directory**: `src/jellyfleet/db/`
**Files**: `base.py`, `models.py`, `migrations/`
**Changes**: Configure SQLAlchemy models (`SyncRun`, optional `SyncDetail`), initialize Alembic migrations, and implement retention utility trimming history to three entries per pair.

#### 2. Repository Layer
**File**: `src/jellyfleet/db/repository.py`
**Changes**: Functions to record run start/end, update status, fetch recent runs, and apply retention.

#### 3. Tests
**File**: `tests/db/test_repository.py`
**Changes**: In-memory SQLite tests for migrations, retention, error cases.

### Success Criteria

#### Automated Verification
- [ ] `uv run alembic upgrade head` succeeds.
- [ ] `uv run pytest tests/db` passes.
- [ ] Coverage ≥85% maintained.

#### Manual Verification
- [ ] Running a simulated sync sequence records entries; after four runs for same pair only three remain.
- [ ] DB file location configurable (default path documented).

---

## Phase 5: Sync Logic (Users, Settings, Libraries)

### Overview
Implement domain-specific synchronization logic, diff computation, dry-run reporting, and execution logging.

### Changes Required

#### 1. Sync Orchestrator
**File**: `src/jellyfleet/sync/orchestrator.py`
**Changes**: Coordinate per-combination sync runs, handle dry-run flag, log structured summaries, persist results via repository, emit DEBUG logs per action.

#### 2. Domain Modules
**Files**:
- `src/jellyfleet/sync/users.py`: Diff father vs child user lists, manage creation/update/deactivation, policy alignment. Determine password handling strategy (likely out of scope; document). Ensure idempotent operations.
- `src/jellyfleet/sync/settings.py`: Compare server/user configuration objects, apply minimal diffs, handle conflicts.
- `src/jellyfleet/sync/libraries.py`: Synchronize libraries, including metadata and access permissions.

#### 3. Diff Utilities
**File**: `src/jellyfleet/sync/diff.py`
**Changes**: Generic diff helpers producing structured results (added/updated/removed with context) used in dry-run output and logging.

#### 4. Tests
**Files**: `tests/sync/test_orchestrator.py`, `tests/sync/test_users.py`, `tests/sync/test_settings.py`, `tests/sync/test_libraries.py`, `tests/sync/test_diff.py`
**Changes**: Mock Jellyfin clients, simulate father/child states, verify API calls, diff outputs, dry-run vs apply behavior, logging instrumentation.

### Success Criteria

#### Automated Verification
- [ ] `uv run pytest tests/sync` passes.
- [ ] Coverage ≥85% maintained.
- [ ] Lint passes for sync modules.

#### Manual Verification
- [ ] `uv run jellyfleet sync --config config/example.yaml --dry-run` logs only planned actions.
- [ ] Removing `--dry-run` applies changes on test Jellyfin instances (manual check) and records accurate DB entries.
- [ ] INFO logs provide concise summary (success/error counts); DEBUG logs detail each action.

---

## Phase 6: Scheduler & CLI Orchestration

### Overview
Deliver CLI entrypoint, cron-based scheduler, and runtime coordination with config, orchestrator, and persistence.

### Changes Required

#### 1. CLI Entrypoint
**File**: `src/jellyfleet/cli.py`
**Changes**: Implement CLI (Typer or Click) with commands:
- `sync` (run once, optional `--dry-run`).
- `scheduler start` (long-running job scheduler).
- `config validate` (schema check).
- `status` (display recent sync history).
Include global flags for config path, DB path, log level.

#### 2. Scheduler Service
**File**: `src/jellyfleet/scheduler.py`
**Changes**: Use APScheduler or croniter-driven loop to schedule sync jobs per config. Default to every 6 hours; warn if cron implies <5 minute intervals. Handle graceful shutdown and overlapping job prevention.

#### 3. Service Runner
**File**: `src/jellyfleet/app.py`
**Changes**: Compose config loader, logger setup, scheduler (if selected), and orchestrator invocation.

#### 4. Tests
**Files**: `tests/test_cli.py`, `tests/test_scheduler.py`
**Changes**: TDD for CLI argument parsing, scheduler cron parsing, short interval warnings, job dispatch in dry-run/apply modes.

### Success Criteria

#### Automated Verification
- [ ] `uv run pytest tests/test_cli.py tests/test_scheduler.py` passes.
- [ ] Coverage ≥85% maintained.
- [ ] `uv run jellyfleet --help` works without runtime errors.

#### Manual Verification
- [ ] Running `uv run jellyfleet scheduler start --config config/example.yaml` schedules jobs, logs next run times, and executes syncs.
- [ ] Cron expressions shorter than 5 minutes emit warnings in logs.
- [ ] Stopping the scheduler updates DB with final run statuses.

---

## Phase 7: Observability, Documentation & Packaging

### Overview
Finalize logging, documentation, sample configurations, Docker packaging, and release readiness.

### Changes Required

#### 1. Logging Profiles
**File**: `src/jellyfleet/logging.py`
**Changes**: Configure structlog (JSON or key-value output), include sync run identifiers, allow runtime log-level override. Ensure INFO minimal, DEBUG verbose.

#### 2. Documentation
**Files**:
- `docs/usage.md`: CLI usage, dry-run, scheduling, log levels.
- `docs/sync-behavior.md`: Domain-specific notes, limitations (e.g., password sync scope).
- `docs/environment.md`: Environment variables, secret file conventions.

#### 3. Samples & Deployment
**File**: `config/example.yaml`
**Changes**: Provide comprehensive sample with multiple fathers/children and domain selections, including env/secret references.

**File**: `docker-compose.yml`
**Changes**: Compose stack with Jellyfleet service, config volume, env file, and scheduler command. Follow mandated field order and comments (allowed in config files) documenting variables.

#### 4. Docker & Build Integration
- Verify Dockerfile works with docker-bake (multi-arch labels, target names).
- Add `make docker-build` and `make docker-run` helpers as needed.

#### 5. Release Preparation
**File**: `docs/release-checklist.md`
**Changes**: Document steps before releasing (tests, coverage, lint, manual dry-run), aligning with semantic-release.

### Success Criteria

#### Automated Verification
- [ ] Full test suite passes: `uv run pytest`.
- [ ] Formatting/lint checks pass: `uv run ruff check .`; `uv run ruff format --check .`.
- [ ] `docker build` and `docker bake` succeed.

#### Manual Verification
- [ ] Sample config syncs between staging Jellyfin instances (manual test).
- [ ] Dry-run output is clear and actionable for operators.
- [ ] Documentation reviewed for completeness and accuracy.

---

## Testing Strategy

- **TDD Discipline**: Write failing tests before adding implementation for each module.
- **Unit Tests**: Focus on config validation, HTTP client behavior (mocked responses), diff calculation, scheduler timing, and database persistence.
- **Integration Tests**: Compose orchestrator tests with mocked Jellyfin responses covering multi-domain sync flows; optional real integration test suite documented for future automation.
- **Coverage**: Maintain ≥85% line/branch coverage via `pytest --cov=src --cov-report=term-missing` enforced locally and in CI.
- **Linting/Formatting**: Incorporate `ruff` checks into CI or pre-commit pipeline.
- **Test Data Management**: Use factories/fixtures for deterministic sample payloads; avoid inline comments per contribution policy.

## Performance & Reliability Considerations

- Recommend cron intervals ≥5 minutes; default 6 hours. Scheduler warns when configuration is shorter.
- Implement exponential backoff on API throttling or network errors, with configurable retry limits.
- Ensure idempotent sync operations to avoid duplicated updates when rerun.
- Retain only last three runs per father-child pair to limit SQLite growth.
- Provide structured logging compatible with centralized log aggregation.

## Migration Notes

- Use Alembic (or equivalent) for schema versioning to support future database evolution.
- Document migration execution steps (`uv run alembic upgrade head`) in release checklist.
- When schema changes occur, include upgrade/downgrade routines preserving existing run history within retention constraints.

## References

- Jellyfin API research: `thoughts/shared/research/2025-10-31-jellyfin-api-sync-capabilities.md`
- Contribution guidelines: `.github/CONTRIBUTING.md`
- Docker build config: `docker-bake.hcl`
