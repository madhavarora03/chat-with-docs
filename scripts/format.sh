#!/usr/bin/env bash
set -euo pipefail
set -x

# Format everything except Alembic migrations
ruff format . --exclude "alembic/versions"

# Organize imports, excluding Alembic migrations
ruff check . --select I --fix --exclude "alembic/versions"

# Lint everything except Alembic versions
ruff check . --exclude "alembic/versions"
