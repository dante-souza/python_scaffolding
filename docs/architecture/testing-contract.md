# Scaffold Testing Contract

## Purpose

Phase 3 tests the scaffold itself rather than only the placeholder application package.

The test suite must prove that environment policy, provenance, the command dispatcher, the Makefile surface, and the shell adapters continue to behave as one coherent contract across supported hosts.

## Test layers

```text
environment.toml
      |
      v
scripts/environment.py
      |
      +--> unit tests: policy, authority state, provenance
      |
      v
scripts/repo.py
      |
      +--> unit tests: handoff and dispatch
      |
      v
Makefile / project.sh / project.ps1
      |
      +--> integration tests: public command surface and bootstrap failures
      |
      v
Windows + Linux CI
```

### Environment-policy unit tests

`tests/test_environment.py` and `tests/test_environment_state.py` cover:

- repository policy loading;
- authority-Python selection;
- authority handoff selection;
- missing or invalid provenance;
- provenance equality and mismatch behavior;
- missing Conda activation;
- Python execution outside the active Conda prefix;
- the current `python -m uv` invocation contract.

These tests must stay independent from Phase 4. They verify the current `authority = "conda"` contract and must not silently introduce native-uv authority.

### Dispatcher tests

`tests/test_repo.py` covers execution behavior after Python has started:

- no unnecessary handoff;
- single-pass authority handoff;
- command and exit-code preservation;
- local dispatch when no handoff is required;
- `help` remaining available without authority activation.

### Command-surface integration tests

`tests/test_command_contract.py` treats the repository entry points as a public interface.

It verifies that:

- Makefile public targets match the dispatcher vocabulary;
- Make targets route through the shared Python dispatcher;
- direct dispatcher help works without an active authority environment;
- unknown commands fail as usage errors rather than environment errors;
- Bash and PowerShell adapters delegate to the shared dispatcher on their native CI host;
- a missing Python bootstrap command produces exit code `127` plus minimal pre-Python diagnostics.

## CI boundary

Phase 3B adds the Windows and Linux CI matrix after this local contract is stable.

CI should execute the same repository tests rather than creating a parallel test definition. Runner setup may provision prerequisites, but it must not duplicate environment-policy logic that belongs to `environment.toml`, `scripts/environment.py`, or the canonical command surface.

## Change rule

When the public command vocabulary changes, update the dispatcher and Makefile together and let the command-contract tests detect drift.

When environment behavior changes, add or update the smallest policy/provenance test that demonstrates the new invariant before changing consumers.
