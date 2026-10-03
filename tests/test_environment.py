from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from environment import (  # noqa: E402
    EnvironmentContractError,
    EnvironmentPolicy,
    expected_provenance,
    inside,
    load_policy,
    normalized,
    provenance_matches,
    uv_module_args,
)


def test_repository_environment_policy_loads() -> None:
    policy = load_policy()

    assert policy.authority == "conda"
    assert policy.venv_name == ".venv"
    assert policy.provenance_file == ".project-source-python.json"
    assert policy.uv_invocation == "python-module"


def test_load_policy_rejects_phase_4_authority_early(tmp_path: Path) -> None:
    config = tmp_path / "environment.toml"
    config.write_text(
        """
[environment]
authority = "uv"
venv = ".venv"
provenance_file = ".project-source-python.json"

[uv]
invocation = "python-module"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(EnvironmentContractError, match="unsupported environment authority"):
        load_policy(config)


def test_inside_detects_child_and_unrelated_paths(tmp_path: Path) -> None:
    parent = tmp_path / "authority"
    child = parent / "bin" / "python"
    unrelated = tmp_path / "other" / "python"

    assert inside(child, parent)
    assert not inside(unrelated, parent)
    assert not inside(child, None)


def test_provenance_matches_normalized_paths(tmp_path: Path) -> None:
    policy = EnvironmentPolicy(
        authority="conda",
        venv_name=".venv",
        provenance_file=".project-source-python.json",
        uv_invocation="python-module",
    )
    python_executable = tmp_path / "conda" / "python"
    prefix = tmp_path / "conda"
    version = "3.12.15"
    metadata = {
        "source_python": normalized(python_executable),
        "source_python_version": version,
        "source_conda_prefix": normalized(prefix),
    }

    assert provenance_matches(
        policy,
        metadata,
        python_executable=python_executable,
        python_version=version,
        authority_prefix=prefix,
    )

    metadata["source_python_version"] = "3.11.0"
    assert not provenance_matches(
        policy,
        metadata,
        python_executable=python_executable,
        python_version=version,
        authority_prefix=prefix,
    )


def test_expected_provenance_requires_authority_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    policy = EnvironmentPolicy(
        authority="conda",
        venv_name=".venv",
        provenance_file=".project-source-python.json",
        uv_invocation="python-module",
    )

    with pytest.raises(EnvironmentContractError, match="cannot build provenance"):
        expected_provenance(policy)


def test_uv_module_args_preserve_existing_invocation_contract() -> None:
    policy = EnvironmentPolicy(
        authority="conda",
        venv_name=".venv",
        provenance_file=".project-source-python.json",
        uv_invocation="python-module",
    )

    assert uv_module_args(policy, "sync", "--python", "python") == [
        "-m",
        "uv",
        "sync",
        "--python",
        "python",
    ]
