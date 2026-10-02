from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv"
IS_WINDOWS = os.name == "nt"
VENV_PYTHON = VENV / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")

TARGETS = {
    "doctor": "Inspect shell/Python/Conda/uv/.venv state and repository policy.",
    "doctor-no-color": "Run environment diagnostics without ANSI colors.",
    "doctor-force-color": "Force ANSI colors in environment diagnostics.",
    "bootstrap": "Install/update uv inside active Conda and create .venv from its Python.",
    "sync": "Synchronize project dependencies into .venv using Conda-local uv.",
    "setup": "bootstrap + sync + doctor.",
    "env-rebuild": "Delete .venv and recreate it from the active Conda Python.",
    "lock": "Refresh uv.lock under the active Conda Python policy.",
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


def require_conda() -> None:
    prefix = os.environ.get("CONDA_PREFIX")
    if not prefix:
        raise SystemExit("ERROR: activate the intended Conda environment first.")
    try:
        common = os.path.commonpath([os.path.abspath(sys.executable), os.path.abspath(prefix)])
    except ValueError:
        common = ""
    if os.path.normcase(common) != os.path.normcase(os.path.abspath(prefix)):
        raise SystemExit("ERROR: current Python is not inside the active Conda environment.")


def require_venv() -> None:
    if not VENV_PYTHON.exists():
        raise SystemExit("ERROR: project .venv is missing. Run: make setup (or ./project.sh setup)")


def cmd_help() -> None:
    print("Project commands (Makefile is canonical; ./project.sh is the Bash adapter):\n")
    width = max(map(len, TARGETS))
    for name, description in TARGETS.items():
        print(f"  make {name:<{width}}  {description}")
    print("\nBash equivalent: ./project.sh <command>")


def cmd_doctor() -> None:
    run_script("doctor.py")


def cmd_doctor_no_color() -> None:
    run_script("doctor.py", "--no-color")


def cmd_doctor_force_color() -> None:
    run_script("doctor.py", "--force-color")


def cmd_bootstrap() -> None:
    run_script("bootstrap.py")


def cmd_sync() -> None:
    require_conda()
    require_venv()
    run(["-m", "uv", "sync", "--python", str(VENV_PYTHON)], executable=Path(sys.executable))


def cmd_lock() -> None:
    require_conda()
    run(["-m", "uv", "lock", "--python", sys.executable], executable=Path(sys.executable))


def cmd_setup() -> None:
    cmd_bootstrap()
    cmd_sync()
    cmd_doctor()


def cmd_env_rebuild() -> None:
    require_conda()
    if VENV.exists():
        print(f"Removing {VENV}")
        shutil.rmtree(VENV)
    cmd_bootstrap()
    cmd_sync()
    cmd_doctor()


def cmd_test() -> None:
    require_venv()
    run(["-m", "pytest"], executable=VENV_PYTHON)


def cmd_lint() -> None:
    require_venv()
    run(["-m", "ruff", "check", "src", "tests", "scripts"], executable=VENV_PYTHON)


def cmd_format() -> None:
    require_venv()
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
    require_venv()
    run(["-m", "project_name"], executable=VENV_PYTHON)


def cmd_clean() -> None:
    dirs = [".pytest_cache", ".ruff_cache", "build", "dist", "htmlcov"]
    for rel in dirs:
        p = ROOT / rel
        if p.exists():
            print(f"Removing {p}")
            shutil.rmtree(p)
    for p in ROOT.rglob("__pycache__"):
        shutil.rmtree(p, ignore_errors=True)
    for p in ROOT.rglob("*.egg-info"):
        if p.is_dir():
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
