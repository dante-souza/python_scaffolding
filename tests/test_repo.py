from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import repo as repo_module  # noqa: E402


def test_handoff_to_authority_skips_subprocess_without_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
