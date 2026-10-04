# Scaffold Testing Contract

## Purpose

The scaffold tests its own environment policy, provenance, command dispatcher,
Makefile surface, shell adapters, and CI topology.

Phase 4 extends that contract from one Python authority to two while preserving
one public lifecycle.

## Test layers

```text
environment.toml
      |
      v
scripts/environment.py
      |
      +--> policy / authority / provenance unit tests
      |
      v
scripts/bootstrap.py + scripts/repo.py + scripts/doctor.py
      |
      +--> bootstrap / dispatch / lifecycle / diagnostics tests
      |
      v
Makefile / project.sh / project.ps1
      |
      +--> command-surface integration tests
      |
      v
.github/workflows/ci.yml
      |
      +--> Linux   / Conda / Make
      +--> Linux   / uv    / Make
      +--> Windows / Conda / Make
      +--> Windows / uv    / Make
```

## Authority tests

The suite proves both authority identities.

Conda tests cover active-prefix requirements, interpreter membership, handoff,
`python -m uv`, legacy provenance compatibility, and Conda-specific mismatch
behavior.

Native-uv tests cover executable discovery, managed-Python installation and
resolution, direct uv invocation, uv-specific provenance, and the absence of a
fake active-environment/re-exec model. Managed-Python discovery explicitly uses
`--system` so the project `.venv` cannot replace the source authority after
bootstrap.

The repository default is `authority = "uv"`. CI temporarily selects
`authority = "conda"` only inside the two Conda matrix workspaces so both
policies run from the same commit.

## Command surface

`tests/test_command_contract.py` treats the repository entry points as a public
interface. It verifies that Makefile targets and the Python dispatcher expose
the same vocabulary and that Bash/PowerShell adapters remain thin.

No authority-specific public target is added. CI must not bypass the contract
with direct `uv sync`, `python -m uv`, pytest, or Ruff lifecycle commands.

## CI proof

Each OS job has a two-authority matrix. All four lanes execute the same sequence:

```text
environment baseline
        |
        v
    make setup
        |
        v
    make check
```

Only runner preparation differs:

- Conda lanes activate a Python 3.12 Conda environment and select
  `authority = "conda"` in that ephemeral checkout.
- uv lanes install the pinned setup-uv action and keep the repository default
  `authority = "uv"`.
- Windows lanes additionally install GNU Make.

Everything after runner preparation is owned by the repository.

## Dependency pinning

External actions are pinned to immutable commit SHAs:

- `actions/checkout` release `v7.0.1`;
- `conda-incubator/setup-miniconda` release `v4.1.0`;
- `astral-sh/setup-uv` release `v10.2.0`.

## Change rule

When the public command vocabulary changes, update the dispatcher and Makefile
together.

When environment behavior changes, update the smallest authority/provenance
tests that demonstrate the invariant.

When CI topology or lifecycle commands change, update
`tests/test_ci_contract.py` in the same commit.
