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

The repository default remains `authority = "conda"` while the native-uv path
is introduced and proven incrementally.

## Phase 4B boundary

Phase 4B owns discovery only:

- locate the native `uv` executable from `PATH`;
- fail closed when native-uv authority is configured but `uv` is unavailable;
- resolve the configured `[python].request` through
  `uv python find --managed-python --no-python-downloads --no-project`;
- require that the resolved interpreter actually exists;
- expose one shared `resolve_authority_python()` boundary for later consumers.

The `--no-python-downloads` flag is deliberate here. Discovery must not mutate
the host. Installing the requested managed Python belongs to bootstrap, which is
introduced in Phase 4C.

## Non-goals of this block

Phase 4B does **not** yet:

- switch the repository default to `authority = "uv"`;
- install a managed Python;
- create or rebuild `.venv` from the native-uv authority;
- change provenance metadata;
- change dispatcher handoff behavior;
- change `doctor` output;
- change CI into a dual-authority matrix.

Those changes depend on the resolution boundary proven here and are handled by
later Phase 4 blocks.

## Invariant

Authority selection and dependency management remain separate responsibilities.

- Under Conda authority, the active Conda environment selects Python and its
  local `python -m uv` performs uv operations.
- Under native-uv authority, the `uv` executable selects a managed Python.
- In both modes, the project `.venv` remains the runtime/dependency boundary
  exposed through the same Makefile targets.
