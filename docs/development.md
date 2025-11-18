# Development Guide

This document describes local development practices for Jellyfleet. For contribution guidelines, see [.github/CONTRIBUTING.md](../.github/CONTRIBUTING.md).

## Environment Setup

### Prerequisites

- Python 3.10+
- uv (Python package manager)
- Docker (for container testing)

### Initial Setup

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

### Environment Variables

Create `.env` file from `.env.example`:

```bash
# Database Configuration
JELLYFLEET_DB_PATH=./jellyfleet.db

# Logging Configuration
JELLYFLEET_LOG_LEVEL=INFO

# Security Configuration
JELLYFLEET_SECRETS_DIR=./secrets
```

## Development Commands

### Code Quality

```bash
# Check code style and potential issues
uv run ruff check .

# Format code automatically
uv run ruff format .

# Check formatting without making changes
uv run ruff format --check .
```

### Testing

```bash
# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run specific test module
uv run pytest tests/config/

# Run specific test function
uv run pytest tests/config/test_loader.py::test_load_valid_config

# Run tests with coverage
uv run pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=src --cov-report=html
```

### Database Operations

```bash
# Run database migrations
uv run alembic upgrade head

# Create new migration
uv run alembic revision --autogenerate -m "description"

# Check migration status
uv run alembic current
uv run alembic history
```

### CLI Development

```bash
# Run CLI with development configuration
uv run jellyfleet --help

# Validate configuration
uv run jellyfleet --config config.yaml validate

# Run sync in dry-run mode
uv run jellyfleet --config config.yaml sync --dry-run
```

## Testing Strategy

### Test Organization

Tests are organized by module:

```
tests/
├── config/          # Configuration loading and validation tests
├── jellyfin/        # Jellyfin client tests
├── sync/           # Synchronization logic tests
├── db/             # Database and repository tests
├── test_cli.py     # CLI interface tests
└── test_imports.py # Import validation tests
```

### Running Test Subsets

```bash
# Configuration tests
uv run pytest tests/config/

# Jellyfin client tests
uv run pytest tests/jellyfin/

# Sync logic tests
uv run pytest tests/sync/

# Database tests
uv run pytest tests/db/

# CLI tests
uv run pytest tests/test_cli.py
```

### Coverage Requirements

- Minimum line coverage: 85%
- Minimum branch coverage: 85%
- Critical path coverage: 100%

Coverage is enforced in CI. Generate local coverage reports:

```bash
# Terminal coverage report
uv run pytest --cov=src --cov-report=term-missing

# HTML coverage report (opens in browser)
uv run pytest --cov=src --cov-report=html && open htmlcov/index.html
```

## Common Troubleshooting

### uv Sync Issues

If `uv sync` fails:

```bash
# Clear uv cache
uv cache clean

# Remove virtual environment
rm -rf .venv

# Retry sync
uv sync
```

### Ruff Issues

If ruff reports unexpected errors:

```bash
# Clear ruff cache
uv run ruff check --clear-cache

# Update ruff
uv add --dev ruff@latest
```

### Test Failures

For test isolation issues:

```bash
# Run tests with fresh database
rm -f test.db jellyfleet.db
uv run pytest

# Run with specific Python path
PYTHONPATH=src uv run pytest
```

### Import Errors

If imports fail in development:

```bash
# Ensure dependencies are installed
uv sync

# Check Python path
uv run python -c "import sys; print(sys.path)"

# Verify package structure
uv run python -c "import jellyfleet; print(jellyfleet.__file__)"
```

### Database Issues

For database-related problems:

```bash
# Reset database
rm -f jellyfleet.db
uv run alembic upgrade head

# Check database connection
uv run python -c "from jellyfleet.db.base import engine; print(engine.url)"
```

## Development Workflow

### Before Committing

```bash
# Run full test suite
uv run pytest

# Check code quality
uv run ruff check .
uv run ruff format --check .

# Verify coverage
uv run pytest --cov=src --cov-report=term-missing
```

### Making Changes

1. Write failing tests first (TDD)
2. Implement minimal code to pass tests
3. Refactor while maintaining test coverage
4. Run full test suite before committing
5. Ensure code passes all quality checks

### Debugging

Enable debug logging:

```bash
# Set debug log level
JELLYFLEET_LOG_LEVEL=DEBUG uv run jellyfleet --config config.yaml sync --dry-run
```

Use pytest debugging:

```bash
# Run with pdb on failure
uv run pytest --pdb

# Run specific test with debugging
uv run pytest tests/config/test_loader.py::test_load_valid_config -s -vv
```

## Performance Considerations

- Use in-memory SQLite for tests when possible
- Mock external API calls in unit tests
- Avoid expensive operations in test setup
- Use fixtures for reusable test data

## Code Standards

Follow the repository's no-comments policy:

- Write self-documenting code
- Use descriptive variable and function names
- Split complex functions into smaller, named functions
- Create documentation files for complex algorithms

See [.github/CONTRIBUTING.md](../.github/CONTRIBUTING.md) for complete contribution guidelines.