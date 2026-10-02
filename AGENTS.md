# AGENTS.md

Repository-wide operating policy for coding agents.

## Read order

Before changing the repository, read:

1. `AGENTS.md`
2. `PROJECT.md`
3. `README.md`
4. the relevant canonical agent under `ai/agents/`
5. the relevant skills under `ai/skills/*/SKILL.md`
6. architecture/ADR documents related to the task

## Precedence

For agent behavior, this file is authoritative over README prose. `PROJECT.md` defines product intent and boundaries. More specific ADRs may constrain implementation choices.

## Mandatory repository rules

- The Makefile is the canonical human-facing command interface.
- Do not introduce recurring direct commands when a Make target should own that workflow.
- Conda selects the Python interpreter/version.
- Do not add `.python-version` or `project.requires-python` under the default environment policy.
- Do not make project automation depend on whichever `uv` happens to appear first on shell `PATH`.
- Use the active Conda Python to invoke `uv` as `python -m uv`.
- Preserve `.venv` provenance tracking.
- Prefer stdlib-only implementation for bootstrap/doctor logic so diagnostics still work before project dependencies are installed.
- Notebooks are exploratory; reusable/reproducible logic belongs in `.py` files.
- Tests and linting are required for behavior-changing code when feasible.
- Update documentation when changing workflow, architecture, environment policy or public behavior.

## Change workflow

1. Inspect existing policy and relevant code.
2. Form a bounded plan for non-trivial changes.
3. Make the smallest coherent change.
4. Add/update tests.
5. Run the narrowest useful checks, then `make check` when appropriate.
6. Update README/PROJECT/ADR material when the contract changes.
7. Report what changed, checks run, and unresolved risks.

## Safety boundaries

Do not silently delete user data, rewrite repository history, rotate credentials, modify external infrastructure, or broaden permissions. Destructive or external actions require explicit task scope and should be isolated from ordinary setup/check targets.

## Canonical agents

- `ai/agents/architect.md`
- `ai/agents/developer.md`
- `ai/agents/reviewer.md`
- `ai/agents/documentation.md`
- `ai/agents/environment.md`

## Canonical skills

- `ai/skills/environment-observability/SKILL.md`
- `ai/skills/makefile-workflow/SKILL.md`
- `ai/skills/testing-quality/SKILL.md`
- `ai/skills/documentation/SKILL.md`

Use `make agents-list`, `make skills-list`, and `make agents-check` to inspect/validate this layer.
