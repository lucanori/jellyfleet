install:
	uv sync

lint:
	uv run ruff check . && uv run ruff format --check .

test:
	uv run pytest

format:
	uv run ruff format .

docker-build:
	docker build -t jellyfleet:dev .