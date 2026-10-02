# Environment Agent

## Mission

Own environment bootstrap, diagnosis and reproducibility boundaries.

## Invariants

- Conda is the Python authority.
- Repository Python pinning is disabled by default.
- `uv` is installed/updated inside the active Conda environment.
- Project automation invokes `uv` through the active Conda Python.
- `.venv` is derived from that interpreter and records provenance.
- A global/external `uv` may coexist but must not silently control project behavior.
- Diagnostic code should remain usable before project dependencies are synchronized.

When changing bootstrap/doctor behavior, update tests/documentation and preserve actionable assessment output.
