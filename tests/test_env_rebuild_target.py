from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import env_rebuild_target as target_module  # noqa: E402
from environment import EnvironmentContractError, EnvironmentPolicy  # noqa: E402


def make_policy(authority: str) -> EnvironmentPolicy:
    return EnvironmentPolicy(
        authority=authority,
        venv_name=".venv",
        provenance_file=".project-source-python.json",
        uv_invocation="python-module",
        python_request="3.12",
    )


def test_conda_rebuild_target_uses_active_authority_python(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    prefix = tmp_path / "conda"
    python = prefix / "python.exe"
    prefix.mkdir()
    python.touch()

    monkeypatch.setattr(target_module, "POLICY", make_policy("conda"))
    monkeypatch.setattr(target_module, "active_authority_prefix", lambda current: prefix)
    monkeypatch.setattr(
        target_module,
        "authority_python_path",
        lambda current, resolved_prefix: python,
    )

    assert target_module.prepare_rebuild_python() == python


def test_uv_rebuild_target_prepares_and_resolves_managed_python(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    uv = tmp_path / "uv.exe"
    uv.touch()
    python = tmp_path / "managed" / "python.exe"
    python.parent.mkdir()
    python.touch()
    calls: list[tuple[list[str], Path, bool, bool, bool]] = []

    monkeypatch.setattr(target_module, "POLICY", make_policy("uv"))
    monkeypatch.setattr(target_module, "require_native_uv", lambda current: uv)
    monkeypatch.setattr(
        target_module,
        "resolve_uv_managed_python",
        lambda current, uv_executable=None: python,
    )

    def fake_run(args, *, cwd, capture_output, text, check):
        calls.append((args, cwd, capture_output, text, check))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(target_module.subprocess, "run", fake_run)

    assert target_module.prepare_rebuild_python() == python
    assert calls == [
        (
            [str(uv), "python", "install", "3.12"],
            target_module.ROOT,
            True,
            True,
            False,
        )
    ]


def test_rebuild_target_rejects_python_inside_project_venv(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    prefix = tmp_path / "conda"
    python = prefix / "python.exe"
    prefix.mkdir()
    python.touch()

    monkeypatch.setattr(target_module, "POLICY", make_policy("conda"))
    monkeypatch.setattr(target_module, "active_authority_prefix", lambda current: prefix)
    monkeypatch.setattr(
        target_module,
        "authority_python_path",
        lambda current, resolved_prefix: python,
    )
    monkeypatch.setattr(target_module, "inside", lambda path, parent: True)

    with pytest.raises(EnvironmentContractError, match="inside the project .venv"):
        target_module.prepare_rebuild_python()
