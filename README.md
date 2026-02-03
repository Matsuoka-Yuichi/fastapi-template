# fastapi-template

A modern FastAPI project template with pre-configured development tools and best practices.

## Features

- **uv** - Fast Python package manager
- **ruff** - Linting and formatting
- **mypy** - Static type checking
- **pre-commit** - Git hooks for code quality

## Quick Start

Install dependencies:
```bash
uv sync --group dev
```

Install pre-commit hooks:
```bash
uv run pre-commit install
```

## Usage

All commands should be run through `uv run`:

```bash
# Run all pre-commit checks
uv run pre-commit run --all-files

# Lint code
uv run ruff check .

# Format code
uv run ruff format .

# Type check
uv run mypy .
```

## Requirements

- Python >= 3.12
- uv
