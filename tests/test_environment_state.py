from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import environment as environment_module  # noqa: E402
from environment import (  # noqa: E402
    EnvironmentContractError,
    EnvironmentPolicy,
    normalized,
    provenance_matches,
    read_provenance,
)


def policy_for(venv: Path) -> EnvironmentPolicy:
    return EnvironmentPolicy(
        authority="conda",
        venv_name=str(venv),
        provenance_file=".project-source-python.json",
        uv_invocation="python-module",
    )


def test_read_provenance_returns_empty_for_missing_file(tmp_path: Path) -> None:
    policy = policy_for(tmp_path / "missing-venv")

    assert read_provenance(policy) == {}


def test_read_provenance_returns_empty_for_invalid_json(tmp_path: Path) -> None:
    venv = tmp_path / "venv"
    venv.mkdir()
    policy = policy_for(venv)
    policy.provenance_path.write_text("{not-json", encoding="utf-8")

    assert read_provenance(policy) == {}


def test_require_active_authority_rejects_missing_conda_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    policy = policy_for(Path(".venv"))

    with pytest.raises(EnvironmentContractError, match="no active conda environment"):
        environment_module.require_active_authority(policy)


def test_require_active_authority_rejects_python_outside_prefix(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    prefix = tmp_path / "conda"
    monkeypatch.setenv("CONDA_PREFIX", str(prefix))
    monkeypatch.setattr(environment_module.sys, "executable", str(tmp_path / "other" / "python"))
    policy = policy_for(tmp_path / "venv")

    with pytest.raises(EnvironmentContractError, match="outside the active conda environment"):
        environment_module.require_active_authority(policy)


def test_provenance_matches_rejects_source_python_mismatch(tmp_path: Path) -> None:
    policy = policy_for(tmp_path / "venv")
    prefix = tmp_path / "conda"
    expected_python = prefix / "python"
    metadata = {
        "source_python": normalized(tmp_path / "different" / "python"),
        "source_python_version": "3.12.15",
        "source_conda_prefix": normalized(prefix),
    }

    assert not provenance_matches(
        policy,
        metadata,
        python_executable=expected_python,
        python_version="3.12.15",
        authority_prefix=prefix,
    )


def test_provenance_matches_rejects_missing_metadata_fields(tmp_path: Path) -> None:
    policy = policy_for(tmp_path / "venv")
    prefix = tmp_path / "conda"
    expected_python = prefix / "python"

    assert not provenance_matches(
        policy,
        {},
        python_executable=expected_python,
        python_version="3.12.15",
        authority_prefix=prefix,
    )
