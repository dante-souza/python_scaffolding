from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import repo as repo_module  # noqa: E402
from environment import EnvironmentPolicy  # noqa: E402


def conda_policy() -> EnvironmentPolicy:
    return EnvironmentPolicy(
        authority="conda",
        venv_name=".venv",
        provenance_file=".project-source-python.json",
        uv_invocation="python-module",
        python_request="3.12",
    )


def uv_policy() -> EnvironmentPolicy:
    return EnvironmentPolicy(
        authority="uv",
        venv_name=".venv",
        provenance_file=".project-source-python.json",
        uv_invocation="python-module",
        python_request="3.12",
    )


def test_handoff_to_authority_skips_subprocess_without_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(repo_module, "POLICY", conda_policy())
    monkeypatch.setattr(
        repo_module,
        "authority_handoff_target",
        lambda policy: None,
    )

    def unexpected_run(*args, **kwargs):
        pytest.fail("subprocess.run must not be called when no handoff target exists")

    monkeypatch.setattr(repo_module.subprocess, "run", unexpected_run)

    assert repo_module.handoff_to_authority() is None


def test_handoff_to_authority_preserves_command_and_exit_code(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    target = tmp_path / "authority-python"
    target.touch()
    calls: list[tuple[list[str], Path, bool]] = []

    monkeypatch.setattr(repo_module, "POLICY", conda_policy())
    monkeypatch.setattr(
        repo_module,
        "authority_handoff_target",
        lambda policy: target,
    )
    monkeypatch.setattr(repo_module.sys, "argv", ["repo.py", "doctor"])

    def fake_run(args, *, cwd, check):
        calls.append((args, cwd, check))
        return SimpleNamespace(returncode=37)

    monkeypatch.setattr(repo_module.subprocess, "run", fake_run)

    assert repo_module.handoff_to_authority() == 37
    assert calls == [
        (
            [
                str(target),
                str(repo_module.ROOT / "scripts" / "repo.py"),
                "doctor",
            ],
            repo_module.ROOT,
            False,
        )
    ]


def test_uv_authority_does_not_reexec_dispatcher(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(repo_module, "POLICY", uv_policy())
    monkeypatch.setattr(
        repo_module,
        "authority_handoff_target",
        lambda policy: pytest.fail("uv mode must not use Conda-style handoff"),
    )
    monkeypatch.setattr(
        repo_module.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("uv mode must not re-exec dispatcher"),
    )

    assert repo_module.handoff_to_authority() is None


def test_windows_env_rebuild_execs_conda_python_outside_project_venv(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    venv = tmp_path / ".venv"
    venv_python = venv / "Scripts" / "python.exe"
    venv_python.parent.mkdir(parents=True)
    venv_python.touch()
    authority_python = tmp_path / "conda" / "python.exe"
    authority_python.parent.mkdir()
    authority_python.touch()

    monkeypatch.setattr(repo_module, "POLICY", conda_policy())
    monkeypatch.setattr(repo_module, "IS_WINDOWS", True)
    monkeypatch.setattr(repo_module, "VENV", venv)
    monkeypatch.setattr(repo_module.sys, "executable", str(venv_python))
    monkeypatch.setattr(repo_module.sys, "argv", ["repo.py", "env-rebuild"])
    monkeypatch.setattr(
        repo_module,
        "authority_handoff_target",
        lambda policy: authority_python,
    )

    calls: list[tuple[str, list[str]]] = []

    def fake_execv(executable: str, argv: list[str]) -> None:
        calls.append((executable, argv))
        raise RuntimeError("exec-called")

    monkeypatch.setattr(repo_module.os, "execv", fake_execv)

    with pytest.raises(RuntimeError, match="exec-called"):
        repo_module.handoff_to_authority()

    assert calls == [
        (
            str(authority_python),
            [
                str(authority_python),
                str(repo_module.ROOT / "scripts" / "repo.py"),
                "env-rebuild",
            ],
        )
    ]


def test_windows_env_rebuild_prepares_and_execs_uv_managed_python(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    venv = tmp_path / ".venv"
    venv_python = venv / "Scripts" / "python.exe"
    venv_python.parent.mkdir(parents=True)
    venv_python.touch()
    uv = tmp_path / "uv.exe"
    uv.touch()
    managed_python = tmp_path / "managed" / "python.exe"
    managed_python.parent.mkdir()
    managed_python.touch()

    monkeypatch.setattr(repo_module, "POLICY", uv_policy())
    monkeypatch.setattr(repo_module, "IS_WINDOWS", True)
    monkeypatch.setattr(repo_module, "VENV", venv)
    monkeypatch.setattr(repo_module.sys, "executable", str(venv_python))
    monkeypatch.setattr(repo_module.sys, "argv", ["repo.py", "env-rebuild"])
    monkeypatch.setattr(repo_module, "require_native_uv", lambda policy: uv)
    monkeypatch.setattr(
        repo_module,
        "resolve_uv_managed_python",
        lambda policy, uv_executable=None: managed_python,
    )

    run_calls: list[tuple[list[str], Path, bool]] = []

    def fake_run(args, *, cwd, check):
        run_calls.append((args, cwd, check))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(repo_module.subprocess, "run", fake_run)

    exec_calls: list[tuple[str, list[str]]] = []

    def fake_execv(executable: str, argv: list[str]) -> None:
        exec_calls.append((executable, argv))
        raise RuntimeError("exec-called")

    monkeypatch.setattr(repo_module.os, "execv", fake_execv)

    with pytest.raises(RuntimeError, match="exec-called"):
        repo_module.handoff_to_authority()

    assert run_calls == [
        (
            [str(uv), "python", "install", "3.12"],
            repo_module.ROOT,
            False,
        )
    ]
    assert exec_calls == [
        (
            str(managed_python),
            [
                str(managed_python),
                str(repo_module.ROOT / "scripts" / "repo.py"),
                "env-rebuild",
            ],
        )
    ]


def test_windows_env_rebuild_escape_is_not_used_for_other_uv_commands(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    venv = tmp_path / ".venv"
    venv_python = venv / "Scripts" / "python.exe"
    venv_python.parent.mkdir(parents=True)
    venv_python.touch()

    monkeypatch.setattr(repo_module, "POLICY", uv_policy())
    monkeypatch.setattr(repo_module, "IS_WINDOWS", True)
    monkeypatch.setattr(repo_module, "VENV", venv)
    monkeypatch.setattr(repo_module.sys, "executable", str(venv_python))
    monkeypatch.setattr(repo_module.sys, "argv", ["repo.py", "doctor"])
    monkeypatch.setattr(
        repo_module.os,
        "execv",
        lambda *args: pytest.fail("doctor must not replace the dispatcher process"),
    )
    monkeypatch.setattr(
        repo_module.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("doctor must not prepare uv rebuild authority"),
    )

    assert repo_module.handoff_to_authority() is None


def test_require_authority_resolves_uv_runtime(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    policy = uv_policy()
    uv = tmp_path / "uv"
    uv.touch()
    python = tmp_path / "managed-python"
    python.touch()

    monkeypatch.setattr(repo_module, "POLICY", policy)
    monkeypatch.setattr(repo_module, "require_native_uv", lambda current: uv)
    monkeypatch.setattr(
        repo_module,
        "resolve_uv_managed_python",
        lambda current, uv_executable=None: python,
    )
    monkeypatch.setattr(
        repo_module,
        "python_executable_version",
        lambda executable: "3.12.15",
    )

    runtime = repo_module.require_authority()

    assert runtime.python == python
    assert runtime.python_version == "3.12.15"
    assert runtime.prefix is None
    assert runtime.uv_executable == uv


def test_cmd_sync_routes_native_uv_to_project_venv(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    policy = uv_policy()
    uv = tmp_path / "uv"
    python = tmp_path / "managed-python"
    venv_python = tmp_path / ".venv" / "python"
    runtime = repo_module.AuthorityRuntime(
        python=python,
        python_version="3.12.15",
        uv_executable=uv,
    )
    calls: list[tuple[list[str], Path | None]] = []

    monkeypatch.setattr(repo_module, "POLICY", policy)
    monkeypatch.setattr(repo_module, "VENV_PYTHON", venv_python)
    monkeypatch.setattr(repo_module, "require_venv_provenance", lambda: runtime)
    monkeypatch.setattr(
        repo_module,
        "run",
        lambda args, executable=None: calls.append((args, executable)),
    )

    repo_module.cmd_sync()

    assert calls == [
        (
            ["sync", "--python", str(venv_python)],
            uv,
        )
    ]


def test_cmd_lock_routes_native_uv_to_authority_python(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    policy = uv_policy()
    uv = tmp_path / "uv"
    python = tmp_path / "managed-python"
    runtime = repo_module.AuthorityRuntime(
        python=python,
        python_version="3.12.15",
        uv_executable=uv,
    )
    calls: list[tuple[list[str], Path | None]] = []

    monkeypatch.setattr(repo_module, "POLICY", policy)
    monkeypatch.setattr(repo_module, "require_authority", lambda: runtime)
    monkeypatch.setattr(
        repo_module,
        "run",
        lambda args, executable=None: calls.append((args, executable)),
    )

    repo_module.cmd_lock()

    assert calls == [
        (
            ["lock", "--python", str(python)],
            uv,
        )
    ]


def test_main_returns_handoff_exit_without_local_command_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    local_calls: list[str] = []

    monkeypatch.setattr(repo_module.sys, "argv", ["repo.py", "doctor"])
    monkeypatch.setattr(repo_module, "handoff_to_authority", lambda: 23)
    monkeypatch.setattr(
        repo_module,
        "cmd_doctor",
        lambda: local_calls.append("doctor"),
    )

    assert repo_module.main() == 23
    assert local_calls == []


def test_main_runs_local_command_once_when_handoff_is_not_needed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    local_calls: list[str] = []

    monkeypatch.setattr(repo_module.sys, "argv", ["repo.py", "doctor"])
    monkeypatch.setattr(repo_module, "handoff_to_authority", lambda: None)
    monkeypatch.setattr(
        repo_module,
        "cmd_doctor",
        lambda: local_calls.append("doctor"),
    )

    assert repo_module.main() == 0
    assert local_calls == ["doctor"]


def test_help_remains_available_without_authority_handoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    help_calls: list[str] = []

    monkeypatch.setattr(repo_module.sys, "argv", ["repo.py", "help"])
    monkeypatch.setattr(
        repo_module,
        "handoff_to_authority",
        lambda: pytest.fail("help must not require an authority handoff"),
    )
    monkeypatch.setattr(
        repo_module,
        "cmd_help",
        lambda: help_calls.append("help"),
    )

    assert repo_module.main() == 0
    assert help_calls == ["help"]
