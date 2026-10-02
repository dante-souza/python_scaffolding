# Skill: Makefile-First Workflow

Use when adding a repeatable developer or automation operation.

## Rules

- Treat Make targets as the canonical public command surface.
- Keep `project.sh` as a thin Bash adapter exposing the same command vocabulary.
- Put complex logic in testable scripts/modules and keep Make recipes and Bash adapters thin.
- Prefer cross-platform Python helpers over shell-heavy recipes.
- Add help text for new routine targets.
- Make failure modes actionable.
- Avoid duplicating environment logic across multiple targets.
- Direct commands may be used for one-off diagnosis, but the final recurring workflow should be represented by the shared dispatcher and exposed by Make; Bash support should route to that same implementation.
