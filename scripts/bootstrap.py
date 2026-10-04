from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from environment import (
    ROOT,
    EnvironmentContractError,
    load_policy,
    provenance_matches,
    provenance_record,
    python_executable_version,
    read_provenance,
    require_active_authority,
    require_native_uv,
    resolve_uv_managed_python,
    uv_module_args,
    uv_python_install_args,
)

POLICY = load_policy()
VENV = POLICY.venv
VENV_PYTHON = POLICY.venv_python
META = POLICY.provenance_path


@dataclass(frozen=True)
class BootstrapAuthority:
    python: Path
    python_version: str
    authority_prefix: Path | None = None
    uv_executable: Path | None = None


def run(*args: str) -> None:
    print("+", " ".join(args))
    subprocess.run(args, cwd=ROOT, check=True)


def prepare_authority() -> BootstrapAuthority:
    if POLICY.authority == "conda":
        authority_prefix = require_active_authority(POLICY)
        authority_python = Path(sys.executable)

        # Conda owns Python, so uv stays local to that authority environment.
        run(sys.executable, "-m", "pip", "install", "--upgrade", "uv")
        run(sys.executable, *uv_module_args(POLICY, "--version"))

        return BootstrapAuthority(
            python=authority_python,
            python_version=sys.version.split()[0],
            authority_prefix=authority_prefix,
        )

    uv = require_native_uv(POLICY)
    run(str(uv), "--version")

    # Bootstrap is the only Phase 4C boundary allowed to install managed Python.
    run(str(uv), *uv_python_install_args(POLICY))
    authority_python = resolve_uv_managed_python(POLICY, uv_executable=uv)
    authority_version = python_executable_version(authority_python)

    return BootstrapAuthority(
        python=authority_python,
        python_version=authority_version,
        uv_executable=uv,
    )


def create_venv(authority: BootstrapAuthority) -> None:
    if POLICY.authority == "conda":
        run(
            str(authority.python),
            *uv_module_args(
                POLICY,
                "venv",
                str(VENV),
                "--python",
                str(authority.python),
            ),
        )
        return

    if authority.uv_executable is None:
        raise EnvironmentContractError(
            "native uv bootstrap is missing its uv executable"
        )

    run(
        str(authority.uv_executable),
        "venv",
        str(VENV),
        "--python",
        str(authority.python),
    )


def provenance_matches_authority(
    metadata: dict,
    authority: BootstrapAuthority,
) -> bool:
    return provenance_matches(
        POLICY,
        metadata,
        python_executable=authority.python,
        python_version=authority.python_version,
        authority_prefix=authority.authority_prefix,
    )


def build_provenance(authority: BootstrapAuthority) -> dict[str, str]:
    return provenance_record(
        POLICY,
        created_by="make bootstrap",
        python_executable=authority.python,
        python_version=authority.python_version,
        authority_prefix=authority.authority_prefix,
        uv_executable=authority.uv_executable,
    )


def main() -> int:
    try:
        authority = prepare_authority()
    except EnvironmentContractError as exc:
        print(f"ERROR: {exc}.")
        if POLICY.authority == "conda":
            print("Activate the intended Conda environment, then run: make bootstrap")
        else:
            print("Install native uv on PATH, then run: make bootstrap")
        return 2

    print(f"{POLICY.authority.title()} Python authority: {authority.python}")
    print(f"Python version: {authority.python_version}")

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

        if not provenance_matches_authority(metadata, authority):
            print(
                "ERROR: project .venv provenance does not match "
                f"the configured {POLICY.authority.title()} Python authority."
            )
            print("Run: make env-rebuild")
            return 3

        print(
            "Existing .venv provenance matches "
            f"the configured {POLICY.authority.title()} authority."
        )
    else:
        try:
            create_venv(authority)
            metadata = build_provenance(authority)
        except EnvironmentContractError as exc:
            print(f"ERROR: {exc}.")
            return 4

        META.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    if not VENV_PYTHON.exists():
        print(f"ERROR: expected venv Python was not created: {VENV_PYTHON}")
        return 4

    print("Bootstrap complete.")
    print("Next: make sync")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
