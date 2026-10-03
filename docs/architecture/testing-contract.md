# Scaffold Testing Contract

## Purpose

Phase 3 tests the scaffold itself rather than only the placeholder application package.

The test suite must prove that environment policy, provenance, the command dispatcher, the Makefile surface, the shell adapters, and CI continue to behave as one coherent contract across supported hosts.

## Test layers

```text
environment.toml
      |
      v
scripts/environment.py
      |
      +--> unit tests: policy, authority state, provenance
      |
      v
scripts/repo.py
      |
      +--> unit tests: handoff and dispatch
      |
      v
Makefile / project.sh / project.ps1
      |
      +--> integration tests: public command surface and bootstrap failures
      |
      v
.github/workflows/ci.yml
      |
      +--> Linux:  Conda + GNU Make + Bash-specific tests
      |
      +--> Windows: Conda + GNU Make + PowerShell-specific tests
```

### Environment-policy unit tests

`tests/test_environment.py` and `tests/test_environment_state.py` cover:

- repository policy loading;
- authority-Python selection;
- authority handoff selection;
- missing or invalid provenance;
- provenance equality and mismatch behavior;
- missing Conda activation;
- Python execution outside the active Conda prefix;
- the current `python -m uv` invocation contract.

These tests must stay independent from Phase 4. They verify the current `authority = "conda"` contract and must not silently introduce native-uv authority.

### Dispatcher tests

`tests/test_repo.py` covers execution behavior after Python has started:

- no unnecessary handoff;
- single-pass authority handoff;
- command and exit-code preservation;
- local dispatch when no handoff is required;
- `help` remaining available without authority activation.

### Command-surface integration tests

`tests/test_command_contract.py` treats the repository entry points as a public interface.

It verifies that:

- Makefile public targets match the dispatcher vocabulary;
- Make targets route through the shared Python dispatcher;
- direct dispatcher help works without an active authority environment;
- unknown commands fail as usage errors rather than environment errors;
- Bash and PowerShell adapters delegate to the shared dispatcher on their native CI host;
- a missing Python bootstrap command produces exit code `127` plus minimal pre-Python diagnostics.

### CI contract tests

`tests/test_ci_contract.py` treats the CI workflow as another scaffold artifact.

It verifies that:

- both `ubuntu-latest` and `windows-latest` remain covered;
- each runner activates the current Conda authority with Python 3.12;
- third-party actions are pinned to reviewed commit SHAs;
- both runners execute `make setup` followed by `make check`;
- Windows explicitly provisions GNU Make;
- feature branches, integration branches, pull requests, and manual dispatch remain represented in the workflow triggers.

## CI boundary

`.github/workflows/ci.yml` is intentionally thin. Runner setup provides Conda and, on Windows, GNU Make. Repository behavior still flows through the same public lifecycle used locally:

```text
Conda authority
      |
      v
make setup
      |
      v
make check
      |
      +--> Ruff
      +--> pytest
      +--> agent/skill validation
```

The Linux job uses `bash -el {0}` so Conda activation survives into each step and the Bash-specific adapter tests execute. The Windows job uses PowerShell, provisions GNU Make, and executes the PowerShell-specific adapter tests.

CI must not reimplement environment policy, provenance validation, dispatcher behavior, or shell-adapter behavior. Those remain owned by `environment.toml`, `scripts/environment.py`, `scripts/repo.py`, and the repository test suite.

## Dependency pinning

External actions are pinned to immutable commit SHAs in the workflow, with their reviewed release tag recorded as a comment. Updating an action is therefore an explicit repository change rather than an implicit moving-tag update.

The initial Phase 3B pins are:

- `actions/checkout` release `v7.0.1`;
- `conda-incubator/setup-miniconda` release `v4.1.0`.

## Change rule

When the public command vocabulary changes, update the dispatcher and Makefile together and let the command-contract tests detect drift.

When environment behavior changes, add or update the smallest policy/provenance test that demonstrates the new invariant before changing consumers.

When CI platform coverage, action versions, or lifecycle commands change, update `tests/test_ci_contract.py` in the same commit.
