from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

from _console import PALETTE_PATH, THEME_PATH, color_enabled, kv, section, style

ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv"
IS_WINDOWS = os.name == "nt"
VENV_PYTHON = VENV / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")
META = VENV / ".project-source-python.json"


def norm(path: str | Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def inside(path: str | Path, parent: str | Path | None) -> bool:
    if not parent:
        return False
    try:
        return os.path.commonpath([norm(path), norm(parent)]) == norm(parent)
    except ValueError:
        return False


def capture(args: list[str]) -> str | None:
    try:
        p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return (p.stdout or p.stderr).strip() or None


def python_probe(executable: Path) -> dict[str, str] | None:
    if not executable.exists():
        return None
    code = (
        "import json,sys; "
        "print(json.dumps({'version':sys.version.split()[0],"
        "'prefix':sys.prefix,'base_prefix':sys.base_prefix,'executable':sys.executable}))"
    )
    raw = capture([str(executable), "-c", code])
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def all_uv_on_path() -> list[Path]:
    names = ["uv.exe", "uv.cmd", "uv.bat", "uv"] if IS_WINDOWS else ["uv"]
    found: list[Path] = []
    seen: set[str] = set()
    for item in os.environ.get("PATH", "").split(os.pathsep):
        if not item:
            continue
        base = Path(item)
        for name in names:
            candidate = base / name
            if candidate.is_file():
                key = norm(candidate)
                if key not in seen:
                    seen.add(key)
                    found.append(candidate)
    return found


def uv_version(path: Path) -> str:
    return capture([str(path), "--version"]) or "<not available>"


def read_meta() -> dict:
    try:
        return json.loads(META.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def read_pyproject() -> dict:
    path = ROOT / "pyproject.toml"
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--no-color", action="store_true")
    group.add_argument("--force-color", action="store_true")
    args = parser.parse_args()
    colors = color_enabled(force=args.force_color, disable=args.no_color)

    conda_prefix = os.environ.get("CONDA_PREFIX")
    conda_active = bool(conda_prefix)
    python_inside_conda = inside(sys.executable, conda_prefix)
    py_version = sys.version.split()[0]

    section("Python / Conda", enabled=colors)
    kv("python", sys.executable, enabled=colors)
    kv("python_version", py_version, enabled=colors)
    kv("conda_active", conda_active, enabled=colors)
    kv("conda_prefix", conda_prefix or "<not active>", enabled=colors)
    kv(
        "python_inside_conda",
        python_inside_conda,
        enabled=colors,
        role="ok" if python_inside_conda else "warning",
    )

    resolved_uv_raw = shutil.which("uv")
    resolved_uv = Path(resolved_uv_raw) if resolved_uv_raw else None
    section("uv resolved by shell PATH", enabled=colors)
    kv("resolved_uv", resolved_uv or "<not found>", enabled=colors)
    kv(
        "resolved_uv_version",
        uv_version(resolved_uv) if resolved_uv else "<not available>",
        enabled=colors,
    )
    kv(
        "resolved_uv_inside_conda",
        inside(resolved_uv, conda_prefix) if resolved_uv else False,
        enabled=colors,
    )

    path_uvs = all_uv_on_path()
    section("uv executables visible on PATH", enabled=colors)
    kv("uv_path_count", len(path_uvs), enabled=colors)
    for idx, item in enumerate(path_uvs):
        scope = "conda" if inside(item, conda_prefix) else "external"
        kv(f"uv_path[{idx}].path", item, enabled=colors)
        kv(f"uv_path[{idx}].scope", scope, enabled=colors)
        kv(f"uv_path[{idx}].version", uv_version(item), enabled=colors)

    conda_uv = None
    if conda_prefix:
        conda_uv = Path(conda_prefix) / ("Scripts/uv.exe" if IS_WINDOWS else "bin/uv")
    conda_uv_exists = bool(conda_uv and conda_uv.exists())
    try:
        uv_pkg = importlib.metadata.version("uv")
    except importlib.metadata.PackageNotFoundError:
        uv_pkg = "<not installed>"

    section("Conda-local uv used by project", enabled=colors)
    kv("conda_uv", conda_uv or "<not available>", enabled=colors)
    kv("conda_uv_exists", conda_uv_exists, enabled=colors)
    kv(
        "conda_uv_version",
        uv_version(conda_uv) if conda_uv_exists else "<not available>",
        enabled=colors,
    )
    kv("conda_uv_package_version", uv_pkg, enabled=colors)
    kv("project_uv_invocation", f"{sys.executable} -m uv", enabled=colors)

    venv_probe = python_probe(VENV_PYTHON)
    meta = read_meta()
    meta_source = meta.get("source_python", "<not recorded>")
    meta_version = meta.get("source_python_version", "<not recorded>")
    meta_conda = meta.get("source_conda_prefix", "<not recorded>")
    source_matches = (
        bool(meta and norm(meta_source) == norm(sys.executable))
        if meta_source != "<not recorded>"
        else False
    )
    version_matches = bool(venv_probe and venv_probe.get("version") == py_version)
    base_prefix_matches = (
        bool(venv_probe and norm(venv_probe.get("base_prefix", "")) == norm(conda_prefix))
        if conda_prefix
        else False
    )

    section("Project .venv", enabled=colors)
    kv("venv_exists", VENV.exists(), enabled=colors)
    kv("venv_python", VENV_PYTHON, enabled=colors)
    kv("venv_python_exists", VENV_PYTHON.exists(), enabled=colors)
    kv(
        "venv_python_version",
        venv_probe.get("version") if venv_probe else "<not available>",
        enabled=colors,
    )
    kv(
        "venv_base_prefix",
        venv_probe.get("base_prefix") if venv_probe else "<not available>",
        enabled=colors,
    )
    kv("venv_source_metadata", META, enabled=colors)
    kv("venv_source_metadata_exists", META.exists(), enabled=colors)
    kv("venv_source_python", meta_source, enabled=colors)
    kv("venv_source_python_version", meta_version, enabled=colors)
    kv("venv_source_conda_prefix", meta_conda, enabled=colors)
    kv("venv_source_matches_active_conda", source_matches, enabled=colors)
    kv("venv_python_version_matches_conda", version_matches, enabled=colors)
    kv("venv_base_prefix_matches_conda", base_prefix_matches, enabled=colors)

    pyproject = read_pyproject()
    requires_python = pyproject.get("project", {}).get("requires-python")
    version_file = (ROOT / ".python-version").exists()
    section("Repository Python policy", enabled=colors)
    kv("python_version_file", version_file, enabled=colors)
    kv("requires_python_declared", bool(requires_python), enabled=colors)
    kv("python_authority", "conda", enabled=colors, role="ok")

    major_minor = ".".join(py_version.split(".")[:2])
    section("uv Python resolution", enabled=colors)
    kv(
        "uv_requires_python_source",
        "pyproject" if requires_python else "interpreter_fallback",
        enabled=colors,
    )
    kv("uv_effective_requires_python", requires_python or f">={major_minor}", enabled=colors)
    kv("uv_resolution_python", sys.executable, enabled=colors)
    kv("uv_resolution_python_version", py_version, enabled=colors)

    section("Doctor console", enabled=colors)
    kv("color_enabled", colors, enabled=colors)
    kv("palette_config", PALETTE_PATH, enabled=colors)
    kv("theme_config", THEME_PATH, enabled=colors)

    errors: list[str] = []
    warnings: list[str] = []
    bootstrap: list[str] = []

    if not conda_active:
        errors.append("No active Conda environment")
    elif not python_inside_conda:
        errors.append("Current Python is outside the active Conda environment")

    if version_file:
        errors.append(".python-version exists, but Conda must be the sole Python authority")
    if requires_python:
        errors.append(
            "pyproject.toml declares requires-python; this template delegates "
            "Python selection to Conda"
        )

    if conda_active and not conda_uv_exists:
        bootstrap.append("Conda-local uv is not installed yet")
    if not VENV.exists():
        bootstrap.append("project .venv does not exist yet")
    elif not VENV_PYTHON.exists():
        errors.append("project .venv exists but its Python executable is missing")
    else:
        if not META.exists():
            warnings.append(".venv provenance metadata is missing")
        elif not source_matches:
            warnings.append(".venv provenance does not match the active Conda Python")
        if not version_matches:
            warnings.append(".venv Python version differs from active Conda Python")
        if conda_prefix and not base_prefix_matches:
            warnings.append(".venv base_prefix differs from the active Conda prefix")

    if resolved_uv and not inside(resolved_uv, conda_prefix):
        warnings.append(
            "the shell resolves 'uv' to an external installation; "
            "project targets intentionally use 'python -m uv'"
        )

    section("Assessment", enabled=colors)
    for item in bootstrap:
        print(style(f"BOOTSTRAP: {item}", "bootstrap", enabled=colors))
    if bootstrap and not errors:
        print(style("ACTION: make bootstrap", "action", enabled=colors))
    for item in warnings:
        print(style(f"WARNING: {item}", "warning", enabled=colors))
    for item in errors:
        print(style(f"ERROR: {item}", "error", enabled=colors))

    if errors:
        print(style("Environment contract: FAILED", "error", enabled=colors))
        return 2

    print(style("Environment contract: OK", "ok", enabled=colors))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
