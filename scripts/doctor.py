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
from dataclasses import dataclass
from pathlib import Path

from _console import PALETTE_PATH, THEME_PATH, color_enabled, kv, section, style
from environment import (
    IS_WINDOWS,
    ROOT,
    EnvironmentContractError,
    active_authority_prefix,
    authority_uv_path,
    inside,
    load_policy,
    normalized,
    provenance_matches,
    read_provenance,
    resolve_authority_python,
    resolve_uv_managed_python,
)

POLICY = load_policy()
VENV = POLICY.venv
VENV_PYTHON = POLICY.venv_python
META = POLICY.provenance_path
AUTHORITY = POLICY.authority.title()


@dataclass(frozen=True)
class AuthorityState:
    prefix: Path | None
    uv_executable: Path | None
    python: Path | None
    python_probe: dict[str, str] | None
    resolution_error: str | None = None


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


def inspect_authority() -> AuthorityState:
    prefix = active_authority_prefix(POLICY)

    if POLICY.authority == "conda":
        uv = authority_uv_path(POLICY, prefix)
        try:
            python = resolve_authority_python(POLICY, authority_prefix=prefix)
        except EnvironmentContractError as exc:
            return AuthorityState(prefix, uv, None, None, str(exc))
        return AuthorityState(prefix, uv, python, python_probe(python))

    uv_raw = shutil.which("uv")
    uv = Path(uv_raw) if uv_raw else None
    if uv is None:
        return AuthorityState(
            None,
            None,
            None,
            None,
            "native uv executable is not available on PATH",
        )

    try:
        python = resolve_uv_managed_python(POLICY, uv_executable=uv)
    except EnvironmentContractError as exc:
        return AuthorityState(None, uv, None, None, str(exc))

    return AuthorityState(None, uv, python, python_probe(python))


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

    state = inspect_authority()
    conda_prefix_raw = os.environ.get("CONDA_PREFIX")
    conda_prefix = Path(conda_prefix_raw) if conda_prefix_raw else None
    current_inside_conda = inside(sys.executable, conda_prefix)
    py_version = sys.version.split()[0]
    authority_version = (
        state.python_probe.get("version") if state.python_probe else None
    )

    section(f"Python / {AUTHORITY} authority", enabled=colors)
    kv("bootstrap_python", sys.executable, enabled=colors)
    kv("bootstrap_python_version", py_version, enabled=colors)
    kv("environment_authority", POLICY.authority, enabled=colors)
    kv("python_request", POLICY.python_request, enabled=colors)
    kv("authority_python", state.python or "<not resolved>", enabled=colors)
    kv("authority_python_version", authority_version or "<not resolved>", enabled=colors)
    kv(
        "authority_resolution_error",
        state.resolution_error or "<none>",
        enabled=colors,
        role="warning" if state.resolution_error else None,
    )
    kv("conda_active", bool(conda_prefix), enabled=colors)
    kv("conda_prefix", conda_prefix or "<not active>", enabled=colors)
    kv("bootstrap_python_inside_conda", current_inside_conda, enabled=colors)

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
        if POLICY.authority == "uv" and resolved_uv and normalized(item) == normalized(resolved_uv):
            scope = "authority"
        elif inside(item, conda_prefix):
            scope = "conda"
        else:
            scope = "external"
        kv(f"uv_path[{idx}].path", item, enabled=colors)
        kv(f"uv_path[{idx}].scope", scope, enabled=colors)
        kv(f"uv_path[{idx}].version", uv_version(item), enabled=colors)

    if POLICY.authority == "conda":
        try:
            uv_pkg = importlib.metadata.version("uv")
        except importlib.metadata.PackageNotFoundError:
            uv_pkg = "<not installed>"
        project_uv = state.uv_executable
        project_uv_invocation = f"{sys.executable} -m uv"
    else:
        uv_pkg = "<not applicable>"
        project_uv = state.uv_executable
        project_uv_invocation = str(project_uv) if project_uv else "<not available>"

    section(f"{AUTHORITY} uv used by project", enabled=colors)
    kv("authority_uv", project_uv or "<not available>", enabled=colors)
    kv("authority_uv_exists", bool(project_uv and project_uv.exists()), enabled=colors)
    kv(
        "authority_uv_version",
        uv_version(project_uv) if project_uv and project_uv.exists() else "<not available>",
        enabled=colors,
    )
    kv("authority_uv_package_version", uv_pkg, enabled=colors)
    kv("project_uv_invocation", project_uv_invocation, enabled=colors)

    venv_probe = python_probe(VENV_PYTHON)
    meta = read_provenance(POLICY)
    meta_source = meta.get("source_python", "<not recorded>")
    meta_version = meta.get("source_python_version", "<not recorded>")
    meta_authority = meta.get("source_authority", "<legacy conda>")
    meta_conda = meta.get("source_conda_prefix", "<not recorded>")
    meta_uv_request = meta.get("source_uv_request", "<not recorded>")

    source_matches = False
    if meta and state.python and authority_version:
        source_matches = provenance_matches(
            POLICY,
            meta,
            python_executable=state.python,
            python_version=authority_version,
            authority_prefix=state.prefix,
        )

    version_matches = bool(
        venv_probe
        and authority_version
        and venv_probe.get("version") == authority_version
    )
    base_prefix_matches = bool(
        venv_probe
        and state.python_probe
        and normalized(venv_probe.get("base_prefix", ""))
        == normalized(state.python_probe.get("prefix", ""))
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
    kv("venv_source_authority", meta_authority, enabled=colors)
    kv("venv_source_python", meta_source, enabled=colors)
    kv("venv_source_python_version", meta_version, enabled=colors)
    kv("venv_source_conda_prefix", meta_conda, enabled=colors)
    kv("venv_source_uv_request", meta_uv_request, enabled=colors)
    kv("venv_source_matches_authority", source_matches, enabled=colors)
    kv("venv_python_version_matches_authority", version_matches, enabled=colors)
    kv("venv_base_prefix_matches_authority", base_prefix_matches, enabled=colors)

    pyproject = read_pyproject()
    requires_python = pyproject.get("project", {}).get("requires-python")
    version_file = (ROOT / ".python-version").exists()
    section("Repository Python policy", enabled=colors)
    kv("python_version_file", version_file, enabled=colors)
    kv("requires_python_declared", bool(requires_python), enabled=colors)
    kv("requires_python", requires_python or "<missing>", enabled=colors)
    kv("python_authority", POLICY.authority, enabled=colors, role="ok")
    kv("configured_python_request", POLICY.python_request, enabled=colors)

    section("Authority Python resolution", enabled=colors)
    kv("authority_request", POLICY.python_request, enabled=colors)
    kv("authority_python", state.python or "<not resolved>", enabled=colors)
    kv("authority_python_version", authority_version or "<not resolved>", enabled=colors)

    section("Doctor console", enabled=colors)
    kv("color_enabled", colors, enabled=colors)
    kv("palette_config", PALETTE_PATH, enabled=colors)
    kv("theme_config", THEME_PATH, enabled=colors)

    errors: list[str] = []
    warnings: list[str] = []
    bootstrap: list[str] = []

    if POLICY.authority == "conda":
        if state.prefix is None:
            errors.append("No active Conda environment")
        elif not inside(sys.executable, state.prefix):
            errors.append("Current Python is outside the active Conda environment")
        if state.resolution_error:
            errors.append(state.resolution_error)
        if state.uv_executable is None or not state.uv_executable.exists():
            bootstrap.append("Conda-local uv is not installed yet")
    else:
        if state.uv_executable is None:
            errors.append("Native uv executable is not available on PATH")
        elif state.python is None:
            detail = state.resolution_error or "managed Python is not resolved"
            bootstrap.append(
                f"uv-managed Python {POLICY.python_request!r} is not ready: {detail}"
            )

    if version_file:
        errors.append(
            ".python-version exists, but environment.toml defines the Python authority"
        )
    if not requires_python:
        errors.append("pyproject.toml does not declare requires-python compatibility")

    if not bash_adapter.is_file():
        errors.append("Bash adapter project.sh is missing")
    elif not IS_WINDOWS and not os.access(bash_adapter, os.X_OK):
        warnings.append("project.sh exists but is not executable; run: chmod +x project.sh")

    if not VENV.exists():
        bootstrap.append("project .venv does not exist yet")
    elif not VENV_PYTHON.exists():
        errors.append("project .venv exists but its Python executable is missing")
    else:
        if not META.exists():
            warnings.append(".venv provenance metadata is missing")
        elif state.python and authority_version and not source_matches:
            warnings.append(
                f".venv provenance does not match configured {AUTHORITY} authority"
            )
        if authority_version and not version_matches:
            warnings.append(
                f".venv Python version differs from configured {AUTHORITY} authority"
            )
        if state.python_probe and not base_prefix_matches:
            warnings.append(
                f".venv base_prefix differs from configured {AUTHORITY} Python"
            )

    if (
        POLICY.authority == "conda"
        and resolved_uv
        and not inside(resolved_uv, state.prefix)
    ):
        warnings.append(
            "the shell resolves 'uv' to an external installation; "
            "Conda-authority targets intentionally use 'python -m uv'"
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
