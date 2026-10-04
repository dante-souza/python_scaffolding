from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "environment.toml"
IS_WINDOWS = os.name == "nt"


class EnvironmentContractError(RuntimeError):
    """Raised when the configured environment contract cannot be satisfied."""


@dataclass(frozen=True)
class EnvironmentPolicy:
    authority: str
    venv_name: str
    provenance_file: str
    uv_invocation: str
    python_request: str = ""

    @property
    def venv(self) -> Path:
        return ROOT / self.venv_name

    @property
    def venv_python(self) -> Path:
        return self.venv / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")

    @property
    def provenance_path(self) -> Path:
        return self.venv / self.provenance_file


def load_policy(path: Path = CONFIG_PATH) -> EnvironmentPolicy:
    try:
        with path.open("rb") as stream:
            raw = tomllib.load(stream)
    except OSError as exc:
        raise EnvironmentContractError(f"environment policy is unavailable: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise EnvironmentContractError(f"environment policy is invalid TOML: {path}") from exc

    environment = raw.get("environment", {})
    python = raw.get("python", {})
    uv = raw.get("uv", {})

    policy = EnvironmentPolicy(
        authority=str(environment.get("authority", "")).strip(),
        venv_name=str(environment.get("venv", "")).strip(),
        provenance_file=str(environment.get("provenance_file", "")).strip(),
        uv_invocation=str(uv.get("invocation", "")).strip(),
        python_request=str(python.get("request", "")).strip(),
    )

    missing = [
        name
        for name, value in (
            ("environment.authority", policy.authority),
            ("environment.venv", policy.venv_name),
            ("environment.provenance_file", policy.provenance_file),
            ("python.request", policy.python_request),
            ("uv.invocation", policy.uv_invocation),
        )
        if not value
    ]
    if missing:
        raise EnvironmentContractError(
            "environment policy is missing required values: " + ", ".join(missing)
        )

    if policy.authority not in {"conda", "uv"}:
        raise EnvironmentContractError(
            f"unsupported environment authority: {policy.authority!r}"
        )
    if policy.uv_invocation != "python-module":
        raise EnvironmentContractError(
            f"unsupported uv invocation: {policy.uv_invocation!r}"
        )

    return policy


def normalized(path: str | Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def inside(path: str | Path, parent: str | Path | None) -> bool:
    if not parent:
        return False
    try:
        return os.path.commonpath([normalized(path), normalized(parent)]) == normalized(parent)
    except ValueError:
        return False


def active_authority_prefix(policy: EnvironmentPolicy) -> Path | None:
    if policy.authority == "conda":
        value = os.environ.get("CONDA_PREFIX")
        return Path(value) if value else None
    return None


def authority_python_path(
    policy: EnvironmentPolicy,
    prefix: str | Path | None = None,
) -> Path | None:
    resolved_prefix = (
        Path(prefix) if prefix is not None else active_authority_prefix(policy)
    )
    if resolved_prefix is None:
        return None
    if policy.authority == "conda":
        return resolved_prefix / ("python.exe" if IS_WINDOWS else "bin/python")
    return None


def native_uv_path(
    policy: EnvironmentPolicy,
    *,
    search_path: str | None = None,
) -> Path | None:
    if policy.authority != "uv":
        return None
    resolved = shutil.which("uv", path=search_path)
    return Path(resolved) if resolved else None


def require_native_uv(
    policy: EnvironmentPolicy,
    *,
    search_path: str | None = None,
) -> Path:
    uv = native_uv_path(policy, search_path=search_path)
    if uv is None:
        raise EnvironmentContractError(
            "native uv authority requires an 'uv' executable on PATH"
        )
    return uv


def authority_handoff_target(
    policy: EnvironmentPolicy,
    *,
    current_python: str | Path = sys.executable,
    authority_prefix: str | Path | None = None,
) -> Path | None:
    target = authority_python_path(policy, authority_prefix)
    if target is None or not target.is_file():
        return None
    if normalized(current_python) == normalized(target):
        return None
    return target


def require_active_authority(policy: EnvironmentPolicy) -> Path:
    prefix = active_authority_prefix(policy)
    if prefix is None:
        raise EnvironmentContractError(
            f"no active {policy.authority} environment; activate the intended environment first"
        )
    if not inside(sys.executable, prefix):
        raise EnvironmentContractError(
            f"current Python is outside the active {policy.authority} environment"
        )
    return prefix


def authority_uv_path(policy: EnvironmentPolicy, prefix: Path | None) -> Path | None:
    if prefix is None or policy.authority != "conda":
        return None
    return prefix / ("Scripts/uv.exe" if IS_WINDOWS else "bin/uv")


def uv_module_args(policy: EnvironmentPolicy, *args: str) -> list[str]:
    if policy.authority != "conda":
        raise EnvironmentContractError(
            "python-module uv invocation is only valid under Conda authority"
        )
    if policy.uv_invocation != "python-module":
        raise EnvironmentContractError(
            f"unsupported uv invocation: {policy.uv_invocation!r}"
        )
    return ["-m", "uv", *args]


def uv_python_install_args(policy: EnvironmentPolicy) -> list[str]:
    if policy.authority != "uv":
        raise EnvironmentContractError(
            "uv-managed Python installation requires authority = 'uv'"
        )
    return ["python", "install", policy.python_request]


def uv_python_find_args(policy: EnvironmentPolicy) -> list[str]:
    if policy.authority != "uv":
        raise EnvironmentContractError(
            "uv-managed Python discovery requires authority = 'uv'"
        )
    return [
        "python",
        "find",
        policy.python_request,
        "--managed-python",
        "--system",
        "--no-python-downloads",
        "--no-project",
    ]


def resolve_uv_managed_python(
    policy: EnvironmentPolicy,
    *,
    uv_executable: str | Path | None = None,
) -> Path:
    if policy.authority != "uv":
        raise EnvironmentContractError(
            "uv-managed Python resolution requires authority = 'uv'"
        )

    uv = Path(uv_executable) if uv_executable is not None else require_native_uv(policy)
    if not uv.is_file():
        raise EnvironmentContractError(f"uv executable does not exist: {uv}")

    completed = subprocess.run(
        [str(uv), *uv_python_find_args(policy)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        suffix = f": {detail}" if detail else ""
        raise EnvironmentContractError(
            "uv could not resolve managed Python "
            f"{policy.python_request!r}{suffix}"
        )

    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        raise EnvironmentContractError(
            "uv returned an unexpected managed-Python discovery result"
        )

    python = Path(lines[0])
    if not python.is_file():
        raise EnvironmentContractError(
            f"uv resolved managed Python to a missing executable: {python}"
        )
    return python


def resolve_authority_python(
    policy: EnvironmentPolicy,
    *,
    authority_prefix: str | Path | None = None,
    uv_executable: str | Path | None = None,
) -> Path:
    if policy.authority == "conda":
        python = authority_python_path(policy, authority_prefix)
        if python is None:
            raise EnvironmentContractError(
                "no active conda environment; activate the intended environment first"
            )
        if not python.is_file():
            raise EnvironmentContractError(
                f"active conda Python executable does not exist: {python}"
            )
        return python

    return resolve_uv_managed_python(policy, uv_executable=uv_executable)


def python_executable_version(executable: str | Path) -> str:
    python = Path(executable)
    if not python.is_file():
        raise EnvironmentContractError(f"Python executable does not exist: {python}")

    completed = subprocess.run(
        [str(python), "-c", "import sys; print(sys.version.split()[0])"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        suffix = f": {detail}" if detail else ""
        raise EnvironmentContractError(
            f"could not query Python version from {python}{suffix}"
        )

    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        raise EnvironmentContractError(
            f"unexpected Python version probe result from {python}"
        )
    return lines[0]


def read_provenance(policy: EnvironmentPolicy) -> dict:
    try:
        return json.loads(policy.provenance_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def expected_provenance(
    policy: EnvironmentPolicy,
    *,
    python_executable: str | Path = sys.executable,
    python_version: str | None = None,
    authority_prefix: str | Path | None = None,
) -> dict[str, str]:
    version = python_version
    if version is None:
        if normalized(python_executable) == normalized(sys.executable):
            version = sys.version.split()[0]
        else:
            version = python_executable_version(python_executable)

    expected = {
        "source_python": normalized(python_executable),
        "source_python_version": version,
    }

    if policy.authority == "conda":
        prefix = (
            Path(authority_prefix)
            if authority_prefix is not None
            else active_authority_prefix(policy)
        )
        if prefix is None:
            raise EnvironmentContractError(
                "cannot build provenance without an active conda environment"
            )
        expected["source_conda_prefix"] = normalized(prefix)
    else:
        expected["source_uv_request"] = policy.python_request

    return expected


def provenance_record(
    policy: EnvironmentPolicy,
    *,
    created_by: str,
    python_executable: str | Path = sys.executable,
    python_version: str | None = None,
    authority_prefix: str | Path | None = None,
    uv_executable: str | Path | None = None,
) -> dict[str, str]:
    record = expected_provenance(
        policy,
        python_executable=python_executable,
        python_version=python_version,
        authority_prefix=authority_prefix,
    )
    record["source_authority"] = policy.authority
    record["created_by"] = created_by

    if policy.authority == "conda":
        record["uv_invocation"] = f"{python_executable} -m uv"
    else:
        if uv_executable is None:
            raise EnvironmentContractError(
                "native uv provenance requires the uv executable path"
            )
        record["uv_invocation"] = str(Path(uv_executable))

    return record


def provenance_matches(
    policy: EnvironmentPolicy,
    metadata: dict,
    *,
    python_executable: str | Path = sys.executable,
    python_version: str | None = None,
    authority_prefix: str | Path | None = None,
) -> bool:
    expected = expected_provenance(
        policy,
        python_executable=python_executable,
        python_version=python_version,
        authority_prefix=authority_prefix,
    )

    if policy.authority == "conda":
        if metadata.get("source_authority", "conda") != "conda":
            return False
        actual = {
            "source_python": normalized(metadata.get("source_python", "")),
            "source_python_version": metadata.get("source_python_version"),
            "source_conda_prefix": normalized(metadata.get("source_conda_prefix", "")),
        }
    else:
        if metadata.get("source_authority") != "uv":
            return False
        actual = {
            "source_python": normalized(metadata.get("source_python", "")),
            "source_python_version": metadata.get("source_python_version"),
            "source_uv_request": metadata.get("source_uv_request"),
        }

    return actual == expected
