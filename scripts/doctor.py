from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

from _console import PALETTE_PATH, THEME_PATH, color_enabled, kv, section, style
from environment import (
    IS_WINDOWS,
    ROOT,
    active_authority_prefix,
    authority_uv_path,
    inside,
    load_policy,
    normalized,
    provenance_matches,
    read_provenance,
)

POLICY = load_policy()
VENV = POLICY.venv
VENV_PYTHON = POLICY.venv_python
META = POLICY.provenance_path
AUTHORITY = POLICY.authority.title()


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
                key = normalized(candidate)
                if key not in seen:
                    seen.add(key)
                    found.append(candidate)
    return found


def uv_version(path: Path) -> str:
    return capture([str(path), "--version"]) or "<not available>"


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

    shell_env = os.environ.get("SHELL")
    bash_raw = shutil.which("bash")
    bash_path = Path(bash_raw) if bash_raw else None
    bash_version_raw = capture([str(bash_path), "--version"]) if bash_path else None
    bash_version = bash_version_raw.splitlines()[0] if bash_version_raw else "<not available>"
    make_raw = shutil.which("make")
    make_path = Path(make_raw) if make_raw else None
    make_version_raw = capture([str(make_path), "--version"]) if make_path else None
    make_version = make_version_raw.splitlines()[0] if make_version_raw else "<not available>"
    bash_adapter = ROOT / "project.sh"

    section("Shell / Platform", enabled=colors)
    kv("platform_system", platform.system(), enabled=colors)
    kv("platform_release", platform.release(), enabled=colors)
    kv("os_name", os.name, enabled=colors)
    kv("shell_env", shell_env or "<not set>", enabled=colors)
    kv("msystem", os.environ.get("MSYSTEM", "<not set>"), enabled=colors)
    kv("bash_available", bool(bash_path), enabled=colors)
    kv("bash_path", bash_path or "<not found>", enabled=colors)
    kv("bash_version", bash_version, enabled=colors)
    kv("bash_adapter", bash_adapter, enabled=colors)
    kv("bash_adapter_exists", bash_adapter.is_file(), enabled=colors)
    kv("make_path", make_path or "<not found>", enabled=colors)
    kv("make_version", make_version, enabled=colors)

    authority_prefix = active_authority_prefix(POLICY)
    authority_active = authority_prefix is not None
    python_inside_authority = inside(sys.executable, authority_prefix)
    py_version = sys.version.split()[0]

    section(f"Python / {AUTHORITY}", enabled=colors)
    kv("python", sys.executable, enabled=colors)
    kv("python_version", py_version, enabled=colors)
    kv("environment_authority", POLICY.authority, enabled=colors)
    kv("conda_active", authority_active, enabled=colors)
    kv("conda_prefix", authority_prefix or "<not active>", enabled=colors)
    kv(
        "python_inside_conda",
        python_inside_authority,
        enabled=colors,
        role="ok" if python_inside_authority else "warning",
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
        inside(resolved_uv, authority_prefix) if resolved_uv else False,
        enabled=colors,
    )

    path_uvs = all_uv_on_path()
    section("uv executables visible on PATH", enabled=colors)
    kv("uv_path_count", len(path_uvs), enabled=colors)
    for idx, item in enumerate(path_uvs):
        scope = POLICY.authority if inside(item, authority_prefix) else "external"
        kv(f"uv_path[{idx}].path", item, enabled=colors)
        kv(f"uv_path[{idx}].scope", scope, enabled=colors)
        kv(f"uv_path[{idx}].version", uv_version(item), enabled=colors)

    authority_uv = authority_uv_path(POLICY, authority_prefix)
    authority_uv_exists = bool(authority_uv and authority_uv.exists())
    try:
        uv_pkg = importlib.metadata.version("uv")
    except importlib.metadata.PackageNotFoundError:
        uv_pkg = "<not installed>"

    section(f"{AUTHORITY}-local uv used by project", enabled=colors)
    kv("conda_uv", authority_uv or "<not available>", enabled=colors)
    kv("conda_uv_exists", authority_uv_exists, enabled=colors)
    kv(
        "conda_uv_version",
        uv_version(authority_uv) if authority_uv_exists and authority_uv else "<not available>",
        enabled=colors,
    )
    kv("conda_uv_package_version", uv_pkg, enabled=colors)
    kv("project_uv_invocation", f"{sys.executable} -m uv", enabled=colors)

    venv_probe = python_probe(VENV_PYTHON)
    meta = read_provenance(POLICY)
    meta_source = meta.get("source_python", "<not recorded>")
    meta_version = meta.get("source_python_version", "<not recorded>")
    meta_conda = meta.get("source_conda_prefix", "<not recorded>")
    source_matches = False
    if meta and authority_prefix:
        source_matches = provenance_matches(
            POLICY,
            meta,
            authority_prefix=authority_prefix,
        )
    version_matches = bool(venv_probe and venv_probe.get("version") == py_version)
    base_prefix_matches = (
        bool(
            venv_probe
            and normalized(venv_probe.get("base_prefix", ""))
            == normalized(authority_prefix)
        )
        if authority_prefix
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
    kv("requires_python", requires_python or "<missing>", enabled=colors)
    kv("python_authority", POLICY.authority, enabled=colors, role="ok")

    section("uv Python resolution", enabled=colors)
    kv(
        "uv_requires_python_source",
        "pyproject" if requires_python else "<missing>",
        enabled=colors,
    )
    kv("uv_effective_requires_python", requires_python or "<missing>", enabled=colors)
    kv("uv_resolution_python", sys.executable, enabled=colors)
    kv("uv_resolution_python_version", py_version, enabled=colors)

    section("Doctor console", enabled=colors)
    kv("color_enabled", colors, enabled=colors)
    kv("palette_config", PALETTE_PATH, enabled=colors)
    kv("theme_config", THEME_PATH, enabled=colors)

    errors: list[str] = []
    warnings: list[str] = []
    bootstrap: list[str] = []

    if not authority_active:
        errors.append(f"No active {AUTHORITY} environment")
    elif not python_inside_authority:
        errors.append(f"Current Python is outside the active {AUTHORITY} environment")

    if version_file:
        errors.append(f".python-version exists, but {AUTHORITY} must be the Python authority")
    if not requires_python:
        errors.append("pyproject.toml does not declare requires-python compatibility")

    if not bash_adapter.is_file():
        errors.append("Bash adapter project.sh is missing")
    elif not IS_WINDOWS and not os.access(bash_adapter, os.X_OK):
        warnings.append("project.sh exists but is not executable; run: chmod +x project.sh")

    if authority_active and not authority_uv_exists:
        bootstrap.append(f"{AUTHORITY}-local uv is not installed yet")
    if not VENV.exists():
        bootstrap.append("project .venv does not exist yet")
    elif not VENV_PYTHON.exists():
        errors.append("project .venv exists but its Python executable is missing")
    else:
        if not META.exists():
            warnings.append(".venv provenance metadata is missing")
        elif not source_matches:
            warnings.append(
                f".venv provenance does not match the active {AUTHORITY} Python"
            )
        if not version_matches:
            warnings.append(f".venv Python version differs from active {AUTHORITY} Python")
        if authority_prefix and not base_prefix_matches:
            warnings.append(
                f".venv base_prefix differs from the active {AUTHORITY} prefix"
            )

    if resolved_uv and not inside(resolved_uv, authority_prefix):
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
