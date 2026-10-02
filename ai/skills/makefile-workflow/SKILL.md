# Skill: Makefile-First Workflow

Use when adding a repeatable developer or automation operation.

## Rules

- Treat Make targets as the stable public command surface.
- Put complex logic in testable scripts/modules and keep Make recipes thin.
- Prefer cross-platform Python helpers over shell-heavy recipes.
- Add help text for new routine targets.
- Make failure modes actionable.
- Avoid duplicating environment logic across multiple targets.
- Direct commands may be used for one-off diagnosis, but the final recurring workflow should be represented by Make.
