from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from environment import (
    ROOT,
    EnvironmentContractError,
    active_authority_prefix,
    authority_python_path,
    inside,
    load_policy,
    require_native_uv,
    resolve_uv_managed_python,
    uv_python_install_args,
)

POLICY = load_policy()


def prepare_rebuild_python() -> Path:
    if POLICY.authority == "conda":
        prefix = active_authority_prefix(POLICY)
        python = authority_python_path(POLICY, prefix)
        if prefix is None or python is None:
            raise EnvironmentContractError(
                "no active conda environment; activate the intended environment first"
            )
        if not python.is_file():
            raise EnvironmentContractError(
                f"active conda Python executable does not exist: {python}"
            )
    else:
        uv = require_native_uv(POLICY)
        completed = subprocess.run(
            [str(uv), *uv_python_install_args(POLICY)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.stdout:
            print(completed.stdout, end="", file=sys.stderr)
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
        if completed.returncode != 0:
            raise EnvironmentContractError(
                f"uv managed-Python preparation failed with exit {completed.returncode}"
            )
        python = resolve_uv_managed_python(POLICY, uv_executable=uv)

    if inside(python, POLICY.venv):
        raise EnvironmentContractError(
            "env-rebuild authority Python resolved inside the project .venv"
        )
    return python


def main() -> int:
    try:
        python = prepare_rebuild_python()
    except EnvironmentContractError as exc:
        print(f"ERROR: {exc}.", file=sys.stderr)
        return 2

    print(python)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
