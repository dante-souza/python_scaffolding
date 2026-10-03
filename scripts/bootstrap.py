from __future__ import annotations

import json
import subprocess
import sys

from environment import (
    ROOT,
    EnvironmentContractError,
    load_policy,
    provenance_matches,
    provenance_record,
    read_provenance,
    require_active_authority,
    uv_module_args,
)

POLICY = load_policy()
VENV = POLICY.venv
VENV_PYTHON = POLICY.venv_python
META = POLICY.provenance_path


def run(*args: str) -> None:
    print("+", " ".join(args))
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> int:
    try:
        authority_prefix = require_active_authority(POLICY)
    except EnvironmentContractError as exc:
        print(f"ERROR: {exc}.")
        print("Activate the intended environment, then run: make bootstrap")
        return 2

    print(f"{POLICY.authority.title()} Python authority: {sys.executable}")
    print(f"Python version: {sys.version.split()[0]}")

    # uv belongs to the configured authority environment, never an unrelated PATH install.
    run(sys.executable, "-m", "pip", "install", "--upgrade", "uv")
    run(sys.executable, *uv_module_args(POLICY, "--version"))

    if VENV.exists():
        if not VENV_PYTHON.exists():
            print(f"ERROR: {VENV.name} exists but its Python executable is missing.")
            print("Run: make env-rebuild")
            return 3
        metadata = read_provenance(POLICY)
        if not metadata:
            print(f"ERROR: {VENV.name} exists without trustworthy source metadata.")
            print("Run: make env-rebuild")
            return 3
        if not provenance_matches(
            POLICY,
            metadata,
            authority_prefix=authority_prefix,
        ):
            print(
                "ERROR: project .venv provenance does not match "
                f"the active {POLICY.authority.title()} Python."
            )
            print("Run: make env-rebuild")
            return 3
        print(
            "Existing .venv provenance matches "
            f"the active {POLICY.authority.title()} environment."
        )
    else:
        run(
            sys.executable,
            *uv_module_args(POLICY, "venv", str(VENV), "--python", sys.executable),
        )
        metadata = provenance_record(
            POLICY,
            authority_prefix=authority_prefix,
            created_by="make bootstrap",
        )
        META.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    if not VENV_PYTHON.exists():
        print(f"ERROR: expected venv Python was not created: {VENV_PYTHON}")
        return 4

    print("Bootstrap complete.")
    print("Next: make sync")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
