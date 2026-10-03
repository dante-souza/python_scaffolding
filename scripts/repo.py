from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from environment import (
    ROOT,
    EnvironmentContractError,
    load_policy,
    provenance_matches,
    read_provenance,
    require_active_authority,
    uv_module_args,
)

POLICY = load_policy()
VENV = POLICY.venv
VENV_PYTHON = POLICY.venv_python
AUTHORITY = POLICY.authority.title()

TARGETS = {
    "doctor": f"Inspect shell/Python/{AUTHORITY}/uv/.venv state and repository policy.",
    "doctor-no-color": "Run environment diagnostics without ANSI colors.",
    "doctor-force-color": "Force ANSI colors in environment diagnostics.",
    "bootstrap": f"Install/update uv inside active {AUTHORITY} and create .venv from its Python.",
    "sync": "Synchronize project dependencies into .venv using authority-local uv.",
    "setup": "bootstrap + sync + doctor.",
    "env-rebuild": f"Delete .venv and recreate it from the active {AUTHORITY} Python.",
    "lock": f"Refresh uv.lock under the active {AUTHORITY} Python policy.",
    "test": "Run pytest.",
    "lint": "Run Ruff checks.",
    "format": "Format source/tests/scripts with Ruff.",
    "check": "Run lint + tests + agent/skill validation.",
    "run": "Run the package entry point.",
    "agents-list": "List canonical AI agent definitions.",
    "skills-list": "List canonical AI skills.",
    "agents-check": "Validate agent/skill scaffold and required policy files.",
    "clean": "Remove generated caches/build artifacts (not .venv).",
}


def run(args: list[str], *, executable: Path | None = None) -> None:
    if executable is not None:
        args = [str(executable), *args]
    print("+", " ".join(args))
    subprocess.run(args, cwd=ROOT, check=True)


def run_script(name: str, *args: str) -> None:
    run([str(ROOT / "scripts" / name), *args], executable=Path(sys.executable))


def require_authority() -> Path:
    try:
        return require_active_authority(POLICY)
    except EnvironmentContractError as exc:
        raise SystemExit(f"ERROR: {exc}.") from None


def require_venv() -> None:
    if not VENV_PYTHON.exists():
        raise SystemExit("ERROR: project .venv is missing. Run: make setup (or ./project.sh setup)")


def require_venv_provenance() -> None:
    authority_prefix = require_authority()
    require_venv()
    metadata = read_provenance(POLICY)
    if not metadata:
        raise SystemExit(
            "ERROR: project .venv provenance is missing or invalid. Run: make env-rebuild"
        )
    if not provenance_matches(
        POLICY,
        metadata,
        authority_prefix=authority_prefix,
    ):
        raise SystemExit(
            "ERROR: project .venv provenance does not match "
            f"the active {AUTHORITY} Python. Run: make env-rebuild"
        )


def cmd_help() -> None:
    print(
        "Project commands "
        "(Makefile is canonical; project.sh and project.ps1 are shell adapters):\n"
    )
    width = max(map(len, TARGETS))
    for name, description in TARGETS.items():
        print(f"  make {name:<{width}}  {description}")
    print("\nShell adapters:")
    print("  Bash:       ./project.sh <command>")
    print(r"  PowerShell: .\project.ps1 <command>")


def cmd_doctor() -> None:
    run_script("doctor.py")


def cmd_doctor_no_color() -> None:
    run_script("doctor.py", "--no-color")


def cmd_doctor_force_color() -> None:
    run_script("doctor.py", "--force-color")


def cmd_bootstrap() -> None:
    run_script("bootstrap.py")


def cmd_sync() -> None:
    require_venv_provenance()
    run(
        uv_module_args(POLICY, "sync", "--python", str(VENV_PYTHON)),
        executable=Path(sys.executable),
    )


def cmd_lock() -> None:
    require_authority()
    run(
        uv_module_args(POLICY, "lock", "--python", sys.executable),
        executable=Path(sys.executable),
    )


def cmd_setup() -> None:
    cmd_bootstrap()
    cmd_sync()
    cmd_doctor()


def cmd_env_rebuild() -> None:
    require_authority()
    if VENV.exists():
        print(f"Removing {VENV}")
        shutil.rmtree(VENV)
    cmd_bootstrap()
    cmd_sync()
    cmd_doctor()


def cmd_test() -> None:
    require_venv_provenance()
    run(["-m", "pytest"], executable=VENV_PYTHON)


def cmd_lint() -> None:
    require_venv_provenance()
    run(["-m", "ruff", "check", "src", "tests", "scripts"], executable=VENV_PYTHON)


def cmd_format() -> None:
    require_venv_provenance()
    run(["-m", "ruff", "format", "src", "tests", "scripts"], executable=VENV_PYTHON)
    run(["-m", "ruff", "check", "--fix", "src", "tests", "scripts"], executable=VENV_PYTHON)


def cmd_agents_list() -> None:
    run_script("agents_check.py", "--list-agents")


def cmd_skills_list() -> None:
    run_script("agents_check.py", "--list-skills")


def cmd_agents_check() -> None:
    run_script("agents_check.py", "--check")


def cmd_check() -> None:
    cmd_lint()
    cmd_test()
    cmd_agents_check()


def cmd_run() -> None:
    require_venv_provenance()
    run(["-m", "project_name"], executable=VENV_PYTHON)


def cmd_clean() -> None:
    dirs = [".pytest_cache", ".ruff_cache", "build", "dist", "htmlcov"]
    for rel in dirs:
        p = ROOT / rel
        if p.is_dir() and not p.is_symlink():
            print(f"Removing {p}")
            shutil.rmtree(p)
        elif p.exists() or p.is_symlink():
            print(f"Removing {p}")
            p.unlink()

    # Never recurse through the whole repository: doing so reaches .venv and can
    # delete interpreter/package caches that belong to the managed environment.
    for base in (ROOT / "src", ROOT / "tests", ROOT / "scripts"):
        if not base.exists():
            continue
        for p in base.rglob("__pycache__"):
            if p.is_dir() and not p.is_symlink():
                shutil.rmtree(p, ignore_errors=True)
        for p in base.rglob("*.egg-info"):
            if p.is_dir() and not p.is_symlink():
                shutil.rmtree(p, ignore_errors=True)


def main() -> int:
    if len(sys.argv) == 1:
        cmd_help()
        return 0
    if len(sys.argv) != 2:
        cmd_help()
        return 2
    command = sys.argv[1].replace("-", "_")
    fn = globals().get(f"cmd_{command}")
    if fn is None:
        print(f"Unknown command: {sys.argv[1]}")
        cmd_help()
        return 2
    try:
        fn()
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
