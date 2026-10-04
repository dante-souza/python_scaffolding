from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import environment as environment_module  # noqa: E402
from environment import (  # noqa: E402
    EnvironmentContractError,
    EnvironmentPolicy,
    native_uv_path,
    require_native_uv,
    resolve_authority_python,
    resolve_uv_managed_python,
)


def uv_policy() -> EnvironmentPolicy:
    return EnvironmentPolicy(
        authority="uv",
        venv_name=".venv",
        provenance_file=".project-source-python.json",
        uv_invocation="python-module",
        python_request="3.12",
    )


def test_native_uv_path_resolves_uv_from_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    uv = tmp_path / ("uv.exe" if environment_module.IS_WINDOWS else "uv")
    uv.touch()
    monkeypatch.setattr(environment_module.shutil, "which", lambda name, path=None: str(uv))

    assert native_uv_path(uv_policy()) == uv


def test_require_native_uv_fails_closed_when_uv_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(environment_module.shutil, "which", lambda name, path=None: None)

    with pytest.raises(EnvironmentContractError, match="requires an 'uv' executable"):
        require_native_uv(uv_policy())


def test_resolve_uv_managed_python_uses_explicit_managed_lookup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    uv = tmp_path / ("uv.exe" if environment_module.IS_WINDOWS else "uv")
    uv.touch()
    python = tmp_path / ("python.exe" if environment_module.IS_WINDOWS else "python")
    python.touch()
    calls: list[tuple[list[str], Path, bool, bool, bool]] = []

    def fake_run(args, *, cwd, capture_output, text, check):
        calls.append((args, cwd, capture_output, text, check))
        return SimpleNamespace(returncode=0, stdout=f"{python}\n", stderr="")

    monkeypatch.setattr(environment_module.subprocess, "run", fake_run)

    assert resolve_uv_managed_python(uv_policy(), uv_executable=uv) == python
    assert calls == [
        (
            [
                str(uv),
                "python",
                "find",
                "3.12",
                "--managed-python",
                "--system",
                "--no-python-downloads",
                "--no-project",
            ],
            environment_module.ROOT,
            True,
            True,
            False,
        )
    ]


def test_managed_python_lookup_explicitly_ignores_project_virtualenv() -> None:
    args = environment_module.uv_python_find_args(uv_policy())

    assert "--managed-python" in args
    assert "--system" in args
    assert "--no-project" in args


def test_resolve_uv_managed_python_reports_discovery_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    uv = tmp_path / ("uv.exe" if environment_module.IS_WINDOWS else "uv")
    uv.touch()

    monkeypatch.setattr(
        environment_module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="No interpreter found",
        ),
    )

    with pytest.raises(
        EnvironmentContractError,
        match="could not resolve managed Python",
    ):
        resolve_uv_managed_python(uv_policy(), uv_executable=uv)


def test_resolve_uv_managed_python_rejects_missing_resolved_executable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    uv = tmp_path / ("uv.exe" if environment_module.IS_WINDOWS else "uv")
    uv.touch()
    missing_python = tmp_path / "missing-python"

    monkeypatch.setattr(
        environment_module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout=f"{missing_python}\n",
            stderr="",
        ),
    )

    with pytest.raises(EnvironmentContractError, match="missing executable"):
        resolve_uv_managed_python(uv_policy(), uv_executable=uv)


def test_resolve_authority_python_delegates_to_uv_managed_python(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    expected = tmp_path / "managed-python"
    calls: list[tuple[EnvironmentPolicy, str | Path | None]] = []

    def fake_resolve(
        policy: EnvironmentPolicy,
        *,
        uv_executable: str | Path | None = None,
    ) -> Path:
        calls.append((policy, uv_executable))
        return expected

    monkeypatch.setattr(environment_module, "resolve_uv_managed_python", fake_resolve)

    policy = uv_policy()
    uv = tmp_path / "uv"

    assert resolve_authority_python(policy, uv_executable=uv) == expected
    assert calls == [(policy, uv)]
