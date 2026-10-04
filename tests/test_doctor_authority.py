from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import doctor as doctor_module  # noqa: E402
from environment import EnvironmentPolicy  # noqa: E402


def uv_policy() -> EnvironmentPolicy:
    return EnvironmentPolicy(
        authority="uv",
        venv_name=".venv",
        provenance_file=".project-source-python.json",
        uv_invocation="python-module",
        python_request="3.12",
    )


def test_inspect_authority_resolves_native_uv_without_conda_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    uv = tmp_path / "uv"
    uv.touch()
    python = tmp_path / "managed-python"
    python.touch()

    monkeypatch.setattr(doctor_module, "POLICY", uv_policy())
    monkeypatch.setattr(doctor_module.shutil, "which", lambda name: str(uv))
    monkeypatch.setattr(
        doctor_module,
        "resolve_uv_managed_python",
        lambda policy, uv_executable=None: python,
    )
    monkeypatch.setattr(
        doctor_module,
        "python_probe",
        lambda executable: {
            "version": "3.12.15",
            "prefix": str(tmp_path / "managed"),
            "base_prefix": str(tmp_path / "managed"),
            "executable": str(python),
        },
    )

    state = doctor_module.inspect_authority()

    assert state.prefix is None
    assert state.uv_executable == uv
    assert state.python == python
    assert state.python_probe is not None
    assert state.python_probe["version"] == "3.12.15"
    assert state.resolution_error is None


def test_inspect_authority_reports_missing_native_uv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(doctor_module, "POLICY", uv_policy())
    monkeypatch.setattr(doctor_module.shutil, "which", lambda name: None)

    state = doctor_module.inspect_authority()

    assert state.prefix is None
    assert state.uv_executable is None
    assert state.python is None
    assert state.python_probe is None
    assert state.resolution_error == "native uv executable is not available on PATH"
