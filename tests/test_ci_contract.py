from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"

CHECKOUT_SHA = "3d3c42e5aac5ba805825da76410c181273ba90b1"
SETUP_MINICONDA_SHA = "be893c923ea9cf1cf7cd510fbdde27c7e18cbdcb"
SETUP_UV_SHA = "c18668ad3cf93ea998bef934396af7bb5c839dc7"


def workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_ci_workflow_covers_linux_and_windows() -> None:
    content = workflow_text()
    assert "runs-on: ubuntu-latest" in content
    assert "runs-on: windows-latest" in content
    assert "shell: bash -el {0}" in content
    assert "shell: pwsh" in content


def test_ci_matrix_proves_both_authorities_on_both_hosts() -> None:
    content = workflow_text()
    assert content.count("- authority: conda") == 2
    assert content.count("- authority: uv") == 2
    assert content.count("SCAFFOLDING_EXPECT_AUTHORITY: ${{ matrix.authority }}") == 2


def test_ci_actions_are_pinned_to_reviewed_commits() -> None:
    content = workflow_text()
    assert content.count(f"actions/checkout@{CHECKOUT_SHA}") == 2
    assert content.count(f"conda-incubator/setup-miniconda@{SETUP_MINICONDA_SHA}") == 2
    assert content.count(f"astral-sh/setup-uv@{SETUP_UV_SHA}") == 2


def test_ci_exercises_same_make_lifecycle_for_every_matrix_lane() -> None:
    content = workflow_text()
    assert content.count("run: make setup") == 2
    assert content.count("run: make check") == 2
    assert "uv sync" not in content
    assert "python -m uv" not in content
    assert "choco install make --yes --no-progress" in content


def test_ci_conda_lane_selects_policy_without_forking_project_commands() -> None:
    content = workflow_text()
    assert content.count("Select Conda policy for this lane") == 2
    assert "s.replace(old,new,1)" in content


def test_ci_runs_on_integration_branches_and_pull_requests() -> None:
    content = workflow_text()
    assert '- "feature/**"' in content
    assert content.count("- main") >= 2
    assert content.count("- dev") >= 2
    assert "pull_request:" in content
    assert "workflow_dispatch:" in content
