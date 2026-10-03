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

## Boundary rule

Finding a Python executable does not make that interpreter the project authority.

The shell only needs a compatible bootstrap interpreter. Once `scripts/repo.py` starts, the shared environment layer resolves the configured authority and hands policy-sensitive commands to its Python interpreter.
