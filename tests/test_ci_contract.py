from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"

CHECKOUT_SHA = "3d3c42e5aac5ba805825da76410c181273ba90b1"
SETUP_MINICONDA_SHA = "be893c923ea9cf1cf7cd510fbdde27c7e18cbdcb"


def workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_ci_workflow_covers_linux_and_windows() -> None:
    content = workflow_text()

    assert "runs-on: ubuntu-latest" in content
    assert "runs-on: windows-latest" in content
    assert "shell: bash -el {0}" in content
    assert "shell: pwsh" in content


def test_ci_uses_current_conda_authority_contract() -> None:
    content = workflow_text()

    assert content.count("activate-environment: python-scaffolding-ci") == 2
    assert content.count('python-version: "3.12"') == 2
    assert "authority = \"uv\"" not in content


def test_ci_actions_are_pinned_to_reviewed_commits() -> None:
    content = workflow_text()

    assert content.count(f"actions/checkout@{CHECKOUT_SHA}") == 2
    assert content.count(f"conda-incubator/setup-miniconda@{SETUP_MINICONDA_SHA}") == 2


def test_ci_exercises_canonical_make_lifecycle_on_both_hosts() -> None:
    content = workflow_text()

    assert content.count("run: make setup") == 2
    assert content.count("run: make check") == 2
    assert "choco install make --yes --no-progress" in content


def test_ci_runs_on_integration_branches_and_pull_requests() -> None:
    content = workflow_text()

    assert '- "feature/**"' in content
    assert content.count("- main") >= 2
    assert content.count("- dev") >= 2
    assert "pull_request:" in content
    assert "workflow_dispatch:" in content
