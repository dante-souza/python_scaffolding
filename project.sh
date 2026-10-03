#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON:-python}"
PYTHON_RESOLVED=""

print_bootstrap_context() {
    printf 'Pre-Python diagnostics:\n' >&2
    printf '  adapter=project.sh\n' >&2
    printf '  repo_root=%s\n' "$ROOT_DIR" >&2
    printf '  shell=bash\n' >&2
    printf '  msystem=%s\n' "${MSYSTEM:-<not set>}" >&2
    printf '  wsl_distro=%s\n' "${WSL_DISTRO_NAME:-<not set>}" >&2
    printf '  python_command=%s\n' "$PYTHON_BIN" >&2
    printf '  python_resolved=%s\n' "${PYTHON_RESOLVED:-<not found>}" >&2
    printf '  conda_prefix=%s\n' "${CONDA_PREFIX:-<not set>}" >&2
    printf '  virtual_env=%s\n' "${VIRTUAL_ENV:-<not set>}" >&2
}

if ! PYTHON_RESOLVED="$(command -v "$PYTHON_BIN" 2>/dev/null)"; then
    printf 'ERROR: Python command not found: %s\n' "$PYTHON_BIN" >&2
    print_bootstrap_context
    printf 'ACTION: activate the intended Python environment in this shell or set PYTHON to its interpreter.\n' >&2
    exit 127
fi

PYTHON_PROBE_OUTPUT=""
if PYTHON_PROBE_OUTPUT="$("$PYTHON_BIN" -c 'import sys; print(sys.executable)' 2>&1)"; then
    :
else
    PYTHON_PROBE_STATUS=$?
    printf 'ERROR: Python command was found but could not be started successfully.\n' >&2
    print_bootstrap_context
    printf '  python_probe_exit=%s\n' "$PYTHON_PROBE_STATUS" >&2
    if [[ -n "$PYTHON_PROBE_OUTPUT" ]]; then
        printf '  python_probe_output=%s\n' "$PYTHON_PROBE_OUTPUT" >&2
    fi
    if [[ -n "${WSL_DISTRO_NAME:-}" || -n "${WSL_INTEROP:-}" ]]; then
        printf 'HINT: WSL needs a Python executable that is runnable inside WSL; a Windows/Cygwin Python inherited through PATH is not a valid substitute.\n' >&2
    fi
    printf 'ACTION: activate the intended Python environment in this shell or set PYTHON to a compatible interpreter.\n' >&2
    exit 126
fi

if (($# == 0)); then
    set -- help
fi

exec "$PYTHON_BIN" scripts/repo.py "$@"
