# Skill: Environment Observability

Use when diagnosing or changing Python/Conda/uv/.venv behavior.

## Procedure

1. Run `make doctor` before mutating the environment.
2. Establish the active Python path/version and `CONDA_PREFIX`.
3. Distinguish shell-resolved `uv` from Conda-local project `uv`.
4. Inspect `.venv` existence, Python version, base prefix and provenance metadata.
5. Check repository policy for `.python-version` and `requires-python` drift.
6. Classify findings as bootstrap requirement, warning or contract error.
7. Prefer the smallest corrective Make target (`make bootstrap`, `make env-rebuild`, `make sync`).
8. Run `make doctor` again after changes.

Do not fix an external `PATH` installation merely because it exists; it is only a problem if the project depends on it or policy requires otherwise.
