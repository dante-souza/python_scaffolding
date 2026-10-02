# ADR-001: Conda is the Python authority

**Status:** Accepted

## Context

The project wants explicit control over the Python interpreter while still using `uv` for fast environment/dependency operations. Multiple independent Python-selection mechanisms would make diagnosis ambiguous.

## Decision

The active Conda environment is the sole Python-version authority. The repository does not use `.python-version` and does not declare `project.requires-python` by default. `uv` is installed inside that Conda environment and invoked as `python -m uv`. The project `.venv` is created from the exact active Conda interpreter and records provenance metadata.

## Consequences

- changing Python means activating/recreating the intended Conda environment, then rebuilding `.venv`;
- a global `uv` may coexist without controlling project targets;
- `make doctor` can distinguish configuration drift from harmless global tooling;
- projects that need distributable package compatibility constraints must deliberately revisit this ADR rather than silently adding a competing authority.
