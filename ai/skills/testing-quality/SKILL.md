# Skill: Testing and Quality Gates

Use when behavior changes or before declaring implementation complete.

## Procedure

1. Identify the narrowest relevant test.
2. Add regression coverage for bugs/fixed behavior.
3. Run `make test` for functional validation.
4. Run `make lint` for static/style validation.
5. Run `make agents-check` if AI policy/scaffold files changed.
6. Run `make check` as the integrated quality gate when dependencies/environment are ready.

Do not weaken a quality rule merely to make the current change pass without documenting the reason.
