from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import repo as repo_module  # noqa: E402


def run_command(
    args: list[str],
    *,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    command_env = os.environ.copy()
    command_env.pop("CONDA_PREFIX", None)
    command_env.pop("VIRTUAL_ENV", None)
    if env:
        command_env.update(env)

    return subprocess.run(
        args,
        cwd=ROOT,
        env=command_env,
        capture_output=True,
        text=True,
        check=False,
    )


def makefile_targets() -> set[str]:
    content = (ROOT / "Makefile").read_text(encoding="utf-8")
    return set(re.findall(r"^([A-Za-z0-9][A-Za-z0-9_-]*):\s*$", content, re.MULTILINE))


def test_makefile_public_targets_match_dispatcher_contract() -> None:
    assert makefile_targets() == {"help", *repo_module.TARGETS}


def test_makefile_routes_public_targets_through_project_cli() -> None:
    content = (ROOT / "Makefile").read_text(encoding="utf-8")

    for target in {"help", *repo_module.TARGETS}:
        pattern = rf"(?m)^{re.escape(target)}:\s*$\n\t@\$\(PROJECT_CLI\) {re.escape(target)}\s*$"
        assert re.search(pattern, content), f"{target!r} bypasses PROJECT_CLI"


def test_repo_help_runs_without_active_authority() -> None:
    completed = run_command([sys.executable, "scripts/repo.py", "help"])

    assert completed.returncode == 0
    assert "Makefile is canonical" in completed.stdout
    assert "make doctor" in completed.stdout


def test_repo_default_command_is_help() -> None:
    completed = run_command([sys.executable, "scripts/repo.py"])

    assert completed.returncode == 0
    assert completed.stdout.startswith("Project commands")


def test_repo_unknown_command_is_usage_error_without_authority() -> None:
    completed = run_command([sys.executable, "scripts/repo.py", "not-a-command"])

    assert completed.returncode == 2
    assert "Unknown command: not-a-command" in completed.stdout


@pytest.mark.skipif(os.name == "nt", reason="Bash adapter is exercised by Linux CI")
def test_bash_adapter_delegates_help_to_shared_dispatcher() -> None:
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash is not available")

    completed = run_command(
        [bash, str(ROOT / "project.sh"), "help"],
        env={"PYTHON": sys.executable},
    )

    assert completed.returncode == 0
    assert "Makefile is canonical" in completed.stdout


@pytest.mark.skipif(os.name != "nt", reason="PowerShell adapter is exercised by Windows CI")
def test_powershell_adapter_delegates_help_to_shared_dispatcher() -> None:
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if powershell is None:
        pytest.skip("PowerShell is not available")

    completed = run_command(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "project.ps1"),
            "help",
        ],
        env={"PYTHON": sys.executable},
    )

    assert completed.returncode == 0
    assert "Makefile is canonical" in completed.stdout


@pytest.mark.skipif(os.name == "nt", reason="Bash startup contract is exercised by Linux CI")
def test_bash_adapter_reports_missing_python_with_exit_127() -> None:
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash is not available")

    completed = run_command(
        [bash, str(ROOT / "project.sh"), "help"],
        env={"PYTHON": "__python_scaffolding_missing_python__"},
    )

    assert completed.returncode == 127
    assert "ERROR: Python command not found" in completed.stderr
    assert "Pre-Python diagnostics:" in completed.stderr
    assert "ACTION:" in completed.stderr


@pytest.mark.skipif(
    os.name != "nt",
    reason="PowerShell startup contract is exercised by Windows CI",
)
def test_powershell_adapter_reports_missing_python_with_exit_127() -> None:
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if powershell is None:
        pytest.skip("PowerShell is not available")

    completed = run_command(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "project.ps1"),
            "help",
        ],
        env={"PYTHON": "__python_scaffolding_missing_python__"},
    )

    assert completed.returncode == 127
    assert "ERROR: Python command not found" in completed.stderr
    assert "Pre-Python diagnostics:" in completed.stderr
    assert "ACTION:" in completed.stderr
