# Authority Bootstrap and Provenance

## Responsibility

Phase 4C gives both supported Python authorities a complete bootstrap path while
preserving the same project `.venv` boundary.

```text
Conda authority                       native uv authority

active Conda env                      uv on PATH
       |                                   |
       v                                   v
current Conda Python                  uv python install <request>
       |                                   |
python -m uv                           uv python find <request>
       |                                   |
       +---------------+-------------------+
                       |
                       v
                create project .venv
                       |
                       v
             record source provenance
```

## Conda mode

Conda behavior remains intentionally compatible with the pre-Phase-4 contract:

1. require an active Conda environment;
2. require the running Python to belong to that environment;
3. install or update `uv` inside the Conda authority;
4. invoke it as `python -m uv`;
5. create `.venv` from the exact Conda interpreter;
6. record the interpreter, version, and Conda prefix.

New Conda provenance records also declare `source_authority = "conda"`.
Legacy Conda records without that field remain valid when every older provenance
field still matches. This avoids forcing existing users to rebuild a correct
environment solely because Phase 4 introduced an explicit authority marker.

## Native uv mode

Native uv bootstrap is deliberately different:

1. require a native `uv` executable on `PATH`;
2. run `uv python install <request>`;
3. resolve that installed interpreter through the non-mutating managed-Python
   discovery boundary from Phase 4B;
4. query the resolved interpreter for its concrete version;
5. create `.venv` with native `uv` using that exact interpreter;
6. record `source_authority = "uv"`, interpreter path/version, and the
   configured Python request.

A `.venv` created under one authority does not silently become valid under the
other. A provenance mismatch fails closed and requires `make env-rebuild`.

## Provenance identity

The authority-specific identity is:

- Conda: source Python path + source Python version + Conda prefix.
- native uv: source Python path + source Python version + configured uv Python
  request.

The uv executable path is recorded for diagnostics but is not part of
provenance equality. Moving or upgrading the uv executable does not by itself
change the Python runtime from which `.venv` was created.

## Phase 4C boundary

This block owns bootstrap, `.venv` creation, and provenance only.

It does not yet make every public lifecycle command dual-authority aware.
Dispatcher handoff, `sync`, `lock`, `doctor`, and the complete public
Makefile lifecycle are handled in the next Phase 4 block.
