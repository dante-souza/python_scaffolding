from __future__ import annotations

import json
import os
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
    uv = raw.get("uv", {})

    policy = EnvironmentPolicy(
        authority=str(environment.get("authority", "")).strip(),
        venv_name=str(environment.get("venv", "")).strip(),
        provenance_file=str(environment.get("provenance_file", "")).strip(),
        uv_invocation=str(uv.get("invocation", "")).strip(),
    )

    missing = [
        name
        for name, value in (
            ("environment.authority", policy.authority),
            ("environment.venv", policy.venv_name),
            ("environment.provenance_file", policy.provenance_file),
            ("uv.invocation", policy.uv_invocation),
        )
        if not value
    ]
    if missing:
        raise EnvironmentContractError(
            "environment policy is missing required values: " + ", ".join(missing)
        )

    # Phase 1 is an architecture extraction, not a policy expansion.
    # Native uv authority is introduced and proven separately in Phase 4.
    if policy.authority != "conda":
        raise EnvironmentContractError(
            f"unsupported environment authority in Phase 1: {policy.authority!r}"
        )
    if policy.uv_invocation != "python-module":
        raise EnvironmentContractError(
            f"unsupported uv invocation in Phase 1: {policy.uv_invocation!r}"
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
    if policy.uv_invocation != "python-module":
        raise EnvironmentContractError(
            f"unsupported uv invocation in Phase 1: {policy.uv_invocation!r}"
        )
    return ["-m", "uv", *args]


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
    prefix = (
        Path(authority_prefix)
        if authority_prefix is not None
        else active_authority_prefix(policy)
    )
    if prefix is None:
        raise EnvironmentContractError(
            f"cannot build provenance without an active {policy.authority} environment"
        )
    return {
        "source_python": normalized(python_executable),
        "source_python_version": python_version or sys.version.split()[0],
        "source_conda_prefix": normalized(prefix),
    }


def provenance_record(
    policy: EnvironmentPolicy,
    *,
    authority_prefix: str | Path,
    created_by: str,
) -> dict[str, str]:
    record = expected_provenance(policy, authority_prefix=authority_prefix)
    record.update(
        {
            "created_by": created_by,
            "uv_invocation": f"{sys.executable} -m uv",
        }
    )
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
    actual = {
        "source_python": normalized(metadata.get("source_python", "")),
        "source_python_version": metadata.get("source_python_version"),
        "source_conda_prefix": normalized(metadata.get("source_conda_prefix", "")),
    }
    return actual == expected
