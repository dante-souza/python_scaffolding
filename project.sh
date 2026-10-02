#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON:-python}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    printf 'ERROR: Python command not found: %s\n' "$PYTHON_BIN" >&2
    printf 'Activate the intended Conda environment or set PYTHON to its interpreter.\n' >&2
    exit 127
fi

if (($# == 0)); then
    set -- help
fi

exec "$PYTHON_BIN" scripts/repo.py "$@"
