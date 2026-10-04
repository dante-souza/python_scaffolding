from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import bootstrap as bootstrap_module  # noqa: E402
from environment import EnvironmentPolicy, normalized  # noqa: E402


def uv_policy() -> EnvironmentPolicy:
    return EnvironmentPolicy(
        authority="uv",
        venv_name=".venv",
        provenance_file=".project-source-python.json",
        uv_invocation="python-module",
        python_request="3.12",
    )


def conda_policy() -> EnvironmentPolicy:
    return EnvironmentPolicy(
        authority="conda",
        venv_name=".venv",
        provenance_file=".project-source-python.json",
        uv_invocation="python-module",
        python_request="3.12",
    )


def set_venv_globals(
    monkeypatch: pytest.MonkeyPatch,
    venv: Path,
) -> Path:
    venv_python = venv / (
        "Scripts/python.exe" if bootstrap_module.sys.platform == "win32" else "bin/python"
    )
    metadata = venv / ".project-source-python.json"

    monkeypatch.setattr(bootstrap_module, "VENV", venv)
    monkeypatch.setattr(bootstrap_module, "VENV_PYTHON", venv_python)
    monkeypatch.setattr(bootstrap_module, "META", metadata)
    return venv_python


def test_uv_bootstrap_installs_managed_python_creates_venv_and_records_provenance(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    policy = uv_policy()
    uv = tmp_path / ("uv.exe" if bootstrap_module.sys.platform == "win32" else "uv")
    uv.touch()
    managed_python = tmp_path / "managed" / (
        "python.exe" if bootstrap_module.sys.platform == "win32" else "python"
    )
    managed_python.parent.mkdir()
    managed_python.touch()

    venv = tmp_path / ".venv"
    venv_python = set_venv_globals(monkeypatch, venv)
    calls: list[list[str]] = []

    monkeypatch.setattr(bootstrap_module, "POLICY", policy)
    monkeypatch.setattr(bootstrap_module, "require_native_uv", lambda current: uv)
    monkeypatch.setattr(
        bootstrap_module,
        "resolve_uv_managed_python",
        lambda current, uv_executable=None: managed_python,
    )
    monkeypatch.setattr(
        bootstrap_module,
        "python_executable_version",
        lambda executable: "3.12.15",
    )

    def fake_run(*args: str) -> None:
        calls.append(list(args))
        if len(args) > 1 and args[1] == "venv":
            venv_python.parent.mkdir(parents=True)
            venv_python.touch()

    monkeypatch.setattr(bootstrap_module, "run", fake_run)

    assert bootstrap_module.main() == 0
    assert calls == [
        [str(uv), "--version"],
        [str(uv), "python", "install", "3.12"],
        [
            str(uv),
            "venv",
            str(venv),
            "--python",
            str(managed_python),
        ],
    ]

    metadata = json.loads(
        (venv / ".project-source-python.json").read_text(encoding="utf-8")
    )
    assert metadata["source_authority"] == "uv"
    assert metadata["source_python"] == normalized(managed_python)
    assert metadata["source_python_version"] == "3.12.15"
    assert metadata["source_uv_request"] == "3.12"
    assert metadata["uv_invocation"] == str(uv)


def test_uv_bootstrap_rejects_venv_from_other_authority(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    policy = uv_policy()
    uv = tmp_path / "uv"
    uv.touch()
    managed_python = tmp_path / "managed-python"
    managed_python.touch()

    venv = tmp_path / ".venv"
    venv_python = set_venv_globals(monkeypatch, venv)
    venv_python.parent.mkdir(parents=True)
    venv_python.touch()
    (venv / ".project-source-python.json").write_text(
        json.dumps(
            {
                "source_authority": "conda",
                "source_python": normalized(managed_python),
                "source_python_version": "3.12.15",
                "source_conda_prefix": normalized(tmp_path / "conda"),
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(bootstrap_module, "POLICY", policy)
    monkeypatch.setattr(bootstrap_module, "require_native_uv", lambda current: uv)
    monkeypatch.setattr(
        bootstrap_module,
        "resolve_uv_managed_python",
        lambda current, uv_executable=None: managed_python,
    )
    monkeypatch.setattr(
        bootstrap_module,
        "python_executable_version",
        lambda executable: "3.12.15",
    )
    monkeypatch.setattr(bootstrap_module, "run", lambda *args: None)

    assert bootstrap_module.main() == 3


def test_conda_bootstrap_preserves_python_module_uv_contract(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    policy = conda_policy()
    prefix = tmp_path / "conda"
    authority_python = prefix / (
        "python.exe" if bootstrap_module.sys.platform == "win32" else "bin/python"
    )
    authority_python.parent.mkdir(parents=True)
    authority_python.touch()

    venv = tmp_path / ".venv"
    venv_python = set_venv_globals(monkeypatch, venv)
    calls: list[list[str]] = []

    monkeypatch.setattr(bootstrap_module, "POLICY", policy)
    monkeypatch.setattr(bootstrap_module.sys, "executable", str(authority_python))
    monkeypatch.setattr(
        bootstrap_module,
        "require_active_authority",
        lambda current: prefix,
    )

    def fake_run(*args: str) -> None:
        calls.append(list(args))
        if "venv" in args:
            venv_python.parent.mkdir(parents=True)
            venv_python.touch()

    monkeypatch.setattr(bootstrap_module, "run", fake_run)

    assert bootstrap_module.main() == 0
    assert calls[0] == [
        str(authority_python),
        "-m",
        "pip",
        "install",
        "--upgrade",
        "uv",
    ]
    assert calls[1] == [str(authority_python), "-m", "uv", "--version"]
    assert calls[2] == [
        str(authority_python),
        "-m",
        "uv",
        "venv",
        str(venv),
        "--python",
        str(authority_python),
    ]

    metadata = json.loads(
        (venv / ".project-source-python.json").read_text(encoding="utf-8")
    )
    assert metadata["source_authority"] == "conda"
    assert metadata["source_python"] == normalized(authority_python)
    assert metadata["source_conda_prefix"] == normalized(prefix)
