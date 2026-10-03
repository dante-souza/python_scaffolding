from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from environment import (  # noqa: E402
    IS_WINDOWS,
    EnvironmentContractError,
    EnvironmentPolicy,
    authority_handoff_target,
    authority_python_path,
    expected_provenance,
    inside,
    load_policy,
    normalized,
    provenance_matches,
    uv_module_args,
    uv_python_find_args,
    uv_python_install_args,
)


def test_repository_environment_policy_loads() -> None:
    policy = load_policy()

    assert policy.authority == "conda"
    assert policy.python_request == "3.12"
    assert policy.venv_name == ".venv"
    assert policy.provenance_file == ".project-source-python.json"
    assert policy.uv_invocation == "python-module"


def test_load_policy_accepts_uv_authority(tmp_path: Path) -> None:
    config = tmp_path / "environment.toml"
    config.write_text(
        """
[environment]
authority = "uv"
venv = ".venv"
provenance_file = ".project-source-python.json"

[python]
request = "3.12"

[uv]
invocation = "python-module"
""".strip(),
        encoding="utf-8",
    )

    policy = load_policy(config)

    assert policy.authority == "uv"
    assert policy.python_request == "3.12"


def test_load_policy_rejects_unknown_authority(tmp_path: Path) -> None:
    config = tmp_path / "environment.toml"
    config.write_text(
        """
[environment]
authority = "unknown"
venv = ".venv"
provenance_file = ".project-source-python.json"

[python]
request = "3.12"

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


def test_authority_python_path_resolves_conda_interpreter(tmp_path: Path) -> None:
    policy = EnvironmentPolicy(
        authority="conda",
        venv_name=".venv",
        provenance_file=".project-source-python.json",
        uv_invocation="python-module",
    )
    prefix = tmp_path / "conda"
    expected = prefix / ("python.exe" if IS_WINDOWS else "bin/python")

    assert authority_python_path(policy, prefix) == expected


def test_authority_handoff_target_requires_existing_authority_python(
    tmp_path: Path,
) -> None:
    policy = EnvironmentPolicy(
        authority="conda",
        venv_name=".venv",
        provenance_file=".project-source-python.json",
        uv_invocation="python-module",
    )
    prefix = tmp_path / "conda"

    assert (
        authority_handoff_target(
            policy,
            current_python=tmp_path / "bootstrap" / "python",
            authority_prefix=prefix,
        )
        is None
    )


def test_authority_handoff_target_skips_when_already_on_authority_python(
    tmp_path: Path,
) -> None:
    policy = EnvironmentPolicy(
        authority="conda",
        venv_name=".venv",
        provenance_file=".project-source-python.json",
        uv_invocation="python-module",
    )
    prefix = tmp_path / "conda"
    authority_python = authority_python_path(policy, prefix)
    assert authority_python is not None
    authority_python.parent.mkdir(parents=True, exist_ok=True)
    authority_python.touch()

    assert (
        authority_handoff_target(
            policy,
            current_python=authority_python,
            authority_prefix=prefix,
        )
        is None
    )


def test_authority_handoff_target_selects_different_authority_python(
    tmp_path: Path,
) -> None:
    policy = EnvironmentPolicy(
        authority="conda",
        venv_name=".venv",
        provenance_file=".project-source-python.json",
        uv_invocation="python-module",
    )
    prefix = tmp_path / "conda"
    authority_python = authority_python_path(policy, prefix)
    assert authority_python is not None
    authority_python.parent.mkdir(parents=True, exist_ok=True)
    authority_python.touch()

    target = authority_handoff_target(
        policy,
        current_python=tmp_path / "bootstrap" / "python",
        authority_prefix=prefix,
    )

    assert target == authority_python


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


def test_uv_authority_builds_explicit_managed_python_commands() -> None:
    policy = EnvironmentPolicy(
        authority="uv",
        venv_name=".venv",
        provenance_file=".project-source-python.json",
        uv_invocation="python-module",
        python_request="3.12",
    )

    assert uv_python_install_args(policy) == ["python", "install", "3.12"]
    assert uv_python_find_args(policy) == [
        "python",
        "find",
        "3.12",
        "--managed-python",
        "--no-python-downloads",
        "--no-project",
    ]


def test_uv_module_args_reject_native_uv_authority() -> None:
    policy = EnvironmentPolicy(
        authority="uv",
        venv_name=".venv",
        provenance_file=".project-source-python.json",
        uv_invocation="python-module",
        python_request="3.12",
    )

    with pytest.raises(
        EnvironmentContractError,
        match="only valid under Conda authority",
    ):
        uv_module_args(policy, "sync")
