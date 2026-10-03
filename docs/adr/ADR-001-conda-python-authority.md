# ADR-001: Conda is the Python authority

**Status:** Accepted

## Context

The project wants explicit control over the Python interpreter while still using `uv` for fast environment/dependency operations. Multiple independent Python-selection mechanisms would make diagnosis ambiguous.

## Decision

The active Conda environment is the Python-version authority: it selects the exact interpreter used by project automation. The repository does not use `.python-version`. It does declare `project.requires-python = ">=3.11"` as a compatibility constraint because the stdlib-only tooling uses Python 3.11 features such as `tomllib`; this constraint does not replace Conda as the interpreter selector. `uv` is installed inside the active Conda environment and invoked as `python -m uv`. The project `.venv` is created from the exact active Conda interpreter and records provenance metadata.

## Consequences

- changing Python means activating/recreating the intended Conda environment, then rebuilding `.venv`;
- a global `uv` may coexist without controlling project targets;
- `make doctor` can distinguish configuration drift from harmless global tooling;
- compatibility constraints and interpreter selection are separate concerns: `requires-python` defines supported runtimes, while Conda chooses the exact runtime used locally;
