from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv"
META = VENV / ".project-source-python.json"
IS_WINDOWS = os.name == "nt"
VENV_PYTHON = VENV / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")


def run(*args: str) -> None:
    print("+", " ".join(args))
    subprocess.run(args, cwd=ROOT, check=True)


def normalized(path: str | Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def inside(path: str | Path, parent: str | Path) -> bool:
    try:
        return os.path.commonpath([normalized(path), normalized(parent)]) == normalized(parent)
    except ValueError:
        return False


def read_metadata() -> dict:
    try:
        return json.loads(META.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def metadata_matches_active_conda(metadata: dict, conda_prefix: str) -> bool:
    source_python = metadata.get("source_python")
    source_version = metadata.get("source_python_version")
    source_conda = metadata.get("source_conda_prefix")
    return bool(
        source_python
        and source_version
        and source_conda
        and normalized(source_python) == normalized(sys.executable)
        and source_version == sys.version.split()[0]
        and normalized(source_conda) == normalized(conda_prefix)
    )


def main() -> int:
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if not conda_prefix:
        print("ERROR: no active Conda environment.")
        print("Activate the intended Conda environment, then run: make bootstrap")
        return 2

    if not inside(sys.executable, conda_prefix):
        print("ERROR: current Python is not inside CONDA_PREFIX.")
        print(f"python={sys.executable}")
        print(f"CONDA_PREFIX={conda_prefix}")
        return 2

    print(f"Conda Python authority: {sys.executable}")
    print(f"Python version: {sys.version.split()[0]}")

    # uv belongs to the active Conda environment, never to an unrelated PATH install.
    run(sys.executable, "-m", "pip", "install", "--upgrade", "uv")
    run(sys.executable, "-m", "uv", "--version")

    if VENV.exists():
        if not VENV_PYTHON.exists():
            print("ERROR: .venv exists but its Python executable is missing.")
            print("Run: make env-rebuild")
            return 3
        metadata = read_metadata()
        if not metadata:
            print("ERROR: .venv exists without trustworthy source metadata.")
            print("Run: make env-rebuild")
            return 3
        if not metadata_matches_active_conda(metadata, conda_prefix):
            print("ERROR: .venv provenance does not match the active Conda Python.")
            print("Run: make env-rebuild")
            return 3
        print("Existing .venv provenance matches the active Conda environment.")
    else:
        run(sys.executable, "-m", "uv", "venv", str(VENV), "--python", sys.executable)
        metadata = {
            "source_python": str(Path(sys.executable).resolve()),
            "source_python_version": sys.version.split()[0],
            "source_conda_prefix": str(Path(conda_prefix).resolve()),
            "created_by": "make bootstrap",
            "uv_invocation": f"{sys.executable} -m uv",
        }
        META.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    if not VENV_PYTHON.exists():
        print(f"ERROR: expected venv Python was not created: {VENV_PYTHON}")
        return 4

    print("Bootstrap complete.")
    print("Next: make sync")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
