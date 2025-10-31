# Jellyfleet

Configuration-driven synchronization service for Jellyfin instances.

## Overview

Jellyfleet propagates users, libraries, and settings across multiple Jellyfin instances arranged in father→child relationships. The service runs on a configurable schedule, supports dry-run mode for testing, and provides structured logging for operational visibility.

## Features

- Configuration-driven sync with YAML files
- Father→child server relationships with selective domain synchronization
- Support for users, libraries, and settings domains
- Dry-run mode for testing changes before application
- Scheduled execution with configurable cron expressions
- SQLite persistence with sync history and retention
- Token-based authentication with multiple secret handling strategies
- Structured logging with configurable verbosity levels

## Architecture

```
src/jellyfleet/
├── config/         # Configuration loading and validation
├── jellyfin/       # Jellyfin API client abstractions
├── sync/           # Domain-specific synchronization logic
├── db/             # SQLite persistence and migrations
├── scheduler.py    # Cron-based job scheduling
├── cli.py          # Command-line interface
└── logging.py      # Structured logging configuration
```

## Requirements

- Python 3.10+
- uv (Python package manager)
- Docker (for containerized deployment)

## Getting Started

### Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd jellyfleet

# Install dependencies
uv sync

# Copy environment template
cp .env.example .env

# Copy configuration template
cp config.example.yaml config.yaml
```

### Configuration

Edit `config.yaml` to define your Jellyfin servers and sync combinations. See [docs/configuration.md](docs/configuration.md) for detailed configuration options.

### Development Commands

```bash
# Run tests
uv run pytest

# Check code quality
uv run ruff check .

# Format code
uv run ruff format .

# Run CLI
uv run jellyfleet --help
```

## Configuration

Jellyfleet uses YAML configuration files to define servers, sync combinations, and runtime settings. For complete configuration documentation, see [docs/configuration.md](docs/configuration.md).

## Development Workflow

### Code Quality

```bash
# Lint code
uv run ruff check .

# Format code
uv run ruff format .

# Run tests with coverage
uv run pytest --cov=src --cov-report=html
```

### Testing

```bash
# Run all tests
uv run pytest

# Run specific test module
uv run pytest tests/config/

# Run with verbose output
uv run pytest -v

# Generate coverage report
uv run pytest --cov=src --cov-report=term-missing
```

### Coverage Requirements

- Minimum line coverage: 85%
- Minimum branch coverage: 85%
- Critical path coverage: 100%

## Docker

### Build

```bash
# Build image
docker build -t jellyfleet:latest .

# Build with docker-bake (multi-arch)
docker bake build
```

### Run

```bash
# Run with configuration
docker run -v $(pwd)/config.yaml:/app/config.yaml \
           -v $(pwd)/.env:/app/.env \
           jellyfleet:latest \
           sync --config /app/config.yaml
```

### Docker Compose

A docker-compose configuration is planned for future phases to simplify deployment.

## Roadmap

- Phase 1: Project scaffolding and tooling ✓
- Phase 2: Configuration system
- Phase 3: Jellyfin client layer
- Phase 4: SQLite persistence and sync history
- Phase 5: Domain-specific sync logic
- Phase 6: Scheduler and CLI orchestration
- Phase 7: Observability and documentation

## Contributing

See [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md) for contribution guidelines, code standards, and development practices.

## License

See LICENSE file for licensing information.