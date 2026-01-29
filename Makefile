.PHONY: serve test lint format check install install-dev clean

# Start the game server
serve:
	uv run --group game uvicorn game.server:app --reload --port 8000

# Run the test suite
test:
	uv run --group dev pytest

# Run linter
lint:
	uv run --group dev ruff check .

# Auto-format code
format:
	uv run --group dev ruff format .

# Run all checks (lint + test)
check: lint test

# Install production dependencies
install:
	uv sync --frozen

# Install all dependencies (dev + game)
install-dev:
	uv sync --frozen --group dev --group game

# Remove build artifacts and caches
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov dist *.egg-info
