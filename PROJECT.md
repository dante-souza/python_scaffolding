# PROJECT

## Identity

**Working name:** Python Project Base  
**Type:** reusable repository scaffold  
**Primary language:** Python  
**Developer interface:** Makefile

## Objective

Provide a dependable starting point for Python repositories that makes environment state explicit, keeps Python-version authority unambiguous, and gives both humans and coding agents the same operational entry points.

## Design principles

1. **Conda is the Python authority.** The active Conda environment selects the interpreter and Python version.
2. **No repository Python pin.** Do not add `.python-version` or `project.requires-python` unless the project deliberately changes this policy.
3. **`uv` is project-controlled.** Bootstrap installs/updates `uv` in the active Conda environment and project automation calls it via `python -m uv`.
4. **`.venv` is reproducible and attributable.** Its source interpreter, Python version and Conda prefix are recorded in `.venv/.project-source-python.json`.
5. **Makefile is the sole routine entry point.** Repeated developer actions should be represented as Make targets.
6. **Observability precedes repair.** `make doctor` explains current state, policy violations, warnings and the next corrective action.
7. **Exploration and production logic are separated.** Notebooks are for exploration; reusable/reproducible logic belongs in Python modules/scripts.
8. **AI guidance has a single canonical source.** Shared agent and skill definitions live under `ai/`; tool-specific directories adapt rather than fork them.
9. **Quality gates are executable.** Tests, linting and AI scaffold validation must be callable from Make.

## Scope

Included in the base scaffold:

- Python `src/` package layout;
- tests;
- notebooks and staged data directories;
- Makefile lifecycle;
- Conda + `uv` bootstrap;
- colorful environment doctor;
- `.venv` provenance tracking;
- Ruff + pytest quality baseline;
- shared agent definitions and reusable skills;
- Codex, Claude and GitHub-facing adapter documentation;
- architecture/ADR documentation placeholders.

## Non-goals

This scaffold does not choose a domain framework, deployment platform, database, cloud provider, notebook platform or application architecture. Those belong to the instantiated project.

## Environment contract

A healthy project satisfies all of the following:

- a Conda environment is active;
- the running `python` belongs to that Conda prefix;
- no `.python-version` file exists;
- `pyproject.toml` does not declare `requires-python`;
- Conda-local `uv` is installed;
- `.venv` exists and was created from the active Conda Python;
- `.venv` provenance metadata matches the active Conda interpreter;
- project workflows use `python -m uv`, not an arbitrary global `uv` executable.

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

When a manual command becomes part of normal project operation, add or update a Make target and document it. When a reusable AI behavior becomes stable, promote it into a focused skill rather than expanding global agent policy indefinitely.
