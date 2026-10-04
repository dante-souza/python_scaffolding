# Phase 4 Closeout — Dual Python Authority

## Result

Phase 4 is functionally complete on the feature branch.

The scaffold now supports two Python-authority modes behind one Makefile contract:

```text
authority = "uv"      authority = "conda"
       |                     |
 native uv              active Conda
       |                     |
 managed Python           Conda Python
        \                   /
         \                 /
            project .venv
                 |
       same Makefile lifecycle
```

Native uv is the reusable-scaffold default. Conda remains fully supported for projects that deliberately want Conda to own interpreter selection.

## Completed blocks

- **4A — policy model:** introduced the explicit Python request and dual authority values.
- **4B — native uv discovery:** added native uv executable and managed-Python resolution.
- **4C — bootstrap/provenance:** created authority-specific bootstrap and `.venv` provenance.
- **4D — lifecycle:** made dispatcher, sync, lock, rebuild, and doctor authority-aware.
- **4E — proof:** exercised Linux/Windows × Conda/uv through the same `make setup` and `make check` lifecycle.

## Corrective invariant discovered by CI

The first 4E native-uv run exposed that `uv python find` could resolve the newly created project `.venv`, causing provenance to fail correctly.

Authority discovery now uses:

```text
uv python find <request>
    --managed-python
    --system
    --no-python-downloads
    --no-project
```

This preserves the separation between **source authority Python** and **project runtime `.venv`**.

## Architectural outcome

```text
                     Makefile
                        |
                  scripts/repo.py
                   /           \
                  /             \
          native uv             Conda
              |                   |
      uv-managed Python       Conda Python
                  \             /
                   \           /
                    project .venv
                         |
             dependencies / tests / run
```

The shell adapters remain thin, environment policy remains centralized, and authority selection does not fork the public command surface.
