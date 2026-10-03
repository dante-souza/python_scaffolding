# Skill: Environment Observability

Use when diagnosing or changing Python/Conda/uv/.venv behavior.

## Procedure

1. Run `make doctor` before mutating the environment.
2. Read `environment.toml` to establish the configured authority and uv invocation.
3. Establish host/shell context, including Bash availability when relevant.
4. Establish the active Python path/version and `CONDA_PREFIX`.
5. Distinguish shell-resolved `uv` from Conda-local project `uv`.
6. Inspect `.venv` existence, Python version, base prefix and provenance metadata.
7. Check repository policy for `.python-version` and `requires-python` drift.
8. Classify findings as bootstrap requirement, warning or contract error.
9. Prefer the smallest corrective Make target (`make bootstrap`, `make env-rebuild`, `make sync`), or its `./project.sh <command>` Bash equivalent.
10. Run `make doctor` again after changes.

Do not fix an external `PATH` installation merely because it exists; it is only a problem if the project depends on it or policy requires otherwise.
