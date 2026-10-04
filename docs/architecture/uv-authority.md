# Native uv Python Authority

## Scope

Phase 4 adds a second Python-authority mode without changing the repository's
public Makefile contract.

The two supported authority models are:

```text
authority = "conda"                 authority = "uv"

active Conda environment            uv executable on PATH
        |                                   |
        v                                   v
Conda-selected Python               uv-managed Python request
        |                                   |
        +-------------+---------------------+
                      |
                      v
                 project .venv
                      |
                      v
             uv-managed dependencies
```

Phase 4 introduced native-uv authority incrementally while preserving the Conda path. After the dual-authority lifecycle passed on Linux and Windows, the reusable scaffold default became `authority = "uv"`.

## Phase 4B boundary

Phase 4B owns discovery only:

- locate the native `uv` executable from `PATH`;
- fail closed when native-uv authority is configured but `uv` is unavailable;
- resolve the configured `[python].request` through
  `uv python find --managed-python --system --no-python-downloads --no-project`;
- require that the resolved interpreter actually exists;
- expose one shared `resolve_authority_python()` boundary for later consumers.

The discovery flags are deliberate. `--no-python-downloads` keeps discovery non-mutating, while `--system` prevents a project `.venv` from becoming the resolved authority after bootstrap. Installing the requested managed Python belongs to bootstrap.

## Historical Phase 4B boundary

Phase 4B intentionally stopped at discovery. Later Phase 4 blocks added managed-Python installation, `.venv` creation, provenance, lifecycle dispatch, diagnostics, the uv-default policy, and the four-lane CI proof. Keeping this boundary documented explains why discovery remains a small reusable primitive instead of absorbing bootstrap behavior.

## Invariant

Authority selection and dependency management remain separate responsibilities.

- Under Conda authority, the active Conda environment selects Python and its
  local `python -m uv` performs uv operations.
- Under native-uv authority, the `uv` executable selects a managed Python.
- In both modes, the project `.venv` remains the runtime/dependency boundary
  exposed through the same Makefile targets.
