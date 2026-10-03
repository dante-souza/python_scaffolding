# Bootstrap Boundary

## Purpose

The shell adapters exist to get far enough to start the shared Python command dispatcher. They are not a second implementation of environment policy.

Phase 2B adds minimal diagnostics for failures that occur before Python can run.

## Responsibility split

```text
Makefile / project.sh / project.ps1
                |
                | bootstrap only
                v
        compatible Python starts
                |
                v
          scripts/repo.py
                |
                | authority handoff
                v
        configured authority Python
                |
                v
 environment.py / doctor.py / bootstrap.py
```

The shell layer may:

- rely on repository attributes that preserve POSIX shell scripts with LF line endings;
- resolve the repository root;
- resolve the requested Python command;
- verify that Python can actually start;
- report basic shell context when startup fails;
- preserve the delegated command's exit code.

The shell layer must not:

- interpret `environment.toml`;
- decide which environment authority is valid;
- inspect or repair uv;
- inspect or repair `.venv` provenance;
- duplicate the Python doctor.

## Pre-Python failure contract

The adapters use conventional command-startup exit codes:

| Exit | Meaning |
|---:|---|
| `126` | Python was resolved, but could not be started successfully. |
| `127` | The requested Python command could not be resolved. |

On either failure, the adapter reports a compact bootstrap context including the repository root, requested/resolved Python command, `CONDA_PREFIX`, and `VIRTUAL_ENV`.

Bash also reports `MSYSTEM` and `WSL_DISTRO_NAME`. When a Python startup failure occurs under WSL, it explains that WSL needs a Python executable runnable inside WSL; inheriting a Windows/Cygwin Python through `PATH` does not create a valid WSL Python environment.

## Authority handoff contract

Phase 2C makes the successful handoff explicit and testable.

`scripts/environment.py` owns handoff selection through `authority_handoff_target()`. The selector returns an authority interpreter only when:

- the configured authority can resolve a Python path;
- that interpreter exists;
- the current bootstrap interpreter is different from the authority interpreter.

`scripts/repo.py` owns execution only: when a target is returned, it re-runs the same command under that interpreter and propagates the child exit code. When no target is returned, dispatch continues in the current interpreter and the existing Python policy checks remain authoritative.

This split prevents the dispatcher from re-encoding authority rules and prevents recursive handoff once execution is already under the authority Python.

The dispatcher behavior is covered separately from environment selection:

- no target means no handoff subprocess is created;
- command arguments are preserved when the command is re-executed;
- the authority child process exit code becomes the dispatcher exit code;
- after a handoff, the bootstrap interpreter does not execute the command locally;
- without a handoff, the local command executes exactly once;
- `help` remains available without requiring authority handoff.

Together with the environment-layer tests that return no target when already running under the authority Python, these checks prove the handoff is single-pass rather than recursive.

## Boundary rule

Finding a Python executable does not make that interpreter the project authority.

The shell only needs a compatible bootstrap interpreter. Once `scripts/repo.py` starts, the shared environment layer decides whether an authority handoff is required before policy-sensitive commands continue.
