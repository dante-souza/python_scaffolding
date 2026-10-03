# PROJECT

## Identity

**Working name:** Python Project Base  
**Type:** reusable repository scaffold  
**Primary language:** Python  
**Developer interface:** Makefile (canonical) + Bash (`project.sh`) and PowerShell (`project.ps1`) adapters

## Objective

Provide a dependable starting point for Python repositories that makes environment state explicit, keeps Python-version authority unambiguous, and gives both humans and coding agents the same operational entry points.

## Design principles

1. **Environment policy is centralized.** `environment.toml` is the declarative source of truth; the current supported authority is `conda`, which selects the interpreter and Python version.
2. **Compatibility is explicit; selection remains with Conda.** `project.requires-python` declares the supported runtime floor (currently Python 3.11+), while the active Conda environment selects the exact interpreter/version. Do not add `.python-version` under the default policy.
3. **Environment policy has one implementation layer.** `scripts/environment.py` interprets authority, authority-Python resolution, handoff selection, uv invocation, `.venv` paths and provenance rules; consumers do not re-encode those decisions independently.
4. **`uv` is project-controlled.** Bootstrap installs/updates `uv` in the active Conda environment and project automation calls it via `python -m uv`.
5. **`.venv` is reproducible and attributable.** Its source interpreter, Python version and Conda prefix are recorded in `.venv/.project-source-python.json`.
6. **Makefile is the canonical routine entry point.** Repeated developer actions should be represented as Make targets; `project.sh` and `project.ps1` mirror that command surface for Bash and PowerShell users and delegate to the same Python dispatcher.
7. **Observability precedes repair.** `make doctor` explains current state, policy violations, warnings and the next corrective action.
8. **Exploration and production logic are separated.** Notebooks are for exploration; reusable/reproducible logic belongs in Python modules/scripts.
9. **AI guidance has a single canonical source.** Shared agent and skill definitions live under `ai/`; tool-specific directories adapt rather than fork them.
10. **Quality gates are executable.** Tests, linting and AI scaffold validation must be callable from Make.

## Scope

Included in the base scaffold:

- Python `src/` package layout;
- tests;
- notebooks and staged data directories;
- Makefile lifecycle;
- Bash and PowerShell adapters with the same command vocabulary and minimal pre-Python startup diagnostics;
- `environment.toml` environment-policy contract;
- shared `scripts/environment.py` policy implementation;
- Conda + `uv` bootstrap for the currently supported authority;
- colorful environment doctor;
- `.venv` provenance tracking;
- Ruff + pytest quality baseline;
- shared agent definitions and reusable skills;
- Codex, Claude and GitHub-facing adapter documentation;
- architecture/ADR documentation placeholders.

## Non-goals

This scaffold does not choose a domain framework, deployment platform, database, cloud provider, notebook platform or application architecture. Those belong to the instantiated project.

## Environment contract

Under the current `authority = "conda"` policy, a healthy project satisfies all of the following:

- a Conda environment is active;
- the running `python` belongs to that Conda prefix;
- no `.python-version` file exists;
- `pyproject.toml` declares `requires-python` compatibility (currently `>=3.11`);
- Conda-local `uv` is installed;
- `.venv` exists and was created from the active Conda Python;
- `.venv` provenance metadata matches the active Conda interpreter;
- project workflows use `python -m uv`, not an arbitrary global `uv` executable;
- Bash and PowerShell support remain thin adapters and do not fork environment-policy or Python-doctor logic;
- shell adapters distinguish Python-not-found (`127`) from Python-found-but-not-startable (`126`) and report only minimal bootstrap context;
- if a shell-local `.venv` shadows the authority Python on `PATH`, `scripts/environment.py` selects the handoff target and the shared dispatcher re-runs the command under that authority interpreter.

An external `uv` on `PATH` is allowed and reported as a warning when it wins shell resolution.

## Standard workflow

```text
make doctor
    ↓
make setup
    ├── bootstrap
    ├── sync
    └── doctor
    ↓
make check
    ├── lint
    ├── test
    └── agents-check
```

## Evolution rule

When a manual command becomes part of normal project operation, add or update the canonical command in `scripts/repo.py`, expose it through Make, and keep the Bash and PowerShell adapters compatible without duplicating implementation logic. Environment-policy changes belong first in `environment.toml` and `scripts/environment.py`; consumers should depend on that shared contract instead of branching on authority themselves. When a reusable AI behavior becomes stable, promote it into a focused skill rather than expanding global agent policy indefinitely.
