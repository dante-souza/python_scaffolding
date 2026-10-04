# ADR-002: Dual Python authority with native uv default

**Status:** Accepted

## Context

ADR-001 established Conda as the sole Python-version authority while uv handled dependency operations. That remains useful when a project deliberately wants Conda to select the interpreter, but it is unnecessarily heavy for repositories whose developers use uv directly.

The scaffold needs both workflows without creating separate Makefiles, bootstrap implementations, or command vocabularies.

## Decision

The scaffold supports two explicit values in `environment.toml`:

- `authority = "uv"`: native uv selects and installs the configured managed-Python request and is the default for newly instantiated repositories;
- `authority = "conda"`: the active Conda environment selects the interpreter, while authority-local uv is invoked as `python -m uv`.

In both modes:

- the public Makefile vocabulary is identical;
- the project runtime/dependency boundary is `.venv`;
- `.venv` records authority-specific source provenance;
- provenance mismatches fail closed and require an explicit rebuild;
- `requires-python` remains a compatibility declaration rather than an exact interpreter selector.

Native-uv authority discovery uses `uv python find --managed-python --system --no-python-downloads --no-project`. The `--system` flag is part of the authority invariant: it prevents the project `.venv` from replacing the uv-managed source Python after bootstrap.

CI proves the contract on Linux and Windows under both authorities using the same `make setup` and `make check` lifecycle.

## Consequences

- native uv becomes the reusable-scaffold default;
- Conda remains a first-class supported authority rather than a legacy path;
- switching authority is a configuration change, not a Makefile/API change;
- dispatcher re-execution remains Conda-specific because Conda is active shell state;
- native uv resolves its managed Python explicitly instead of emulating an active environment;
- CI cost increases from two lanes to four in exchange for direct end-to-end proof of the dual-authority contract.

## Supersedes

ADR-001 as the statement that Conda is the sole authority. Its Conda-specific mechanics remain valid under the `authority = "conda"` branch of this decision.
