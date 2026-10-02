# Python Project Base

Reusable repository scaffold for Python projects with a **Makefile-first workflow**, a **Bash command adapter**, **Conda-owned Python selection**, **Conda-local `uv`**, explicit `.venv` provenance, colorful environment diagnostics, and a shared agent/skill layer.

The template is intentionally opinionated about **workflow**, not about the Python version: there is no `.python-version` and no `requires-python` declaration. The active Conda environment is the authority.

## Core contract

```text
Conda environment
  └── chooses Python interpreter/version
          │
          ▼
 active Python
  ├── installs/updates uv inside Conda
  ├── invokes uv as: python -m uv
  └── creates project .venv from this exact interpreter
          │
          ▼
 project .venv
  ├── receives project dependencies
  └── records source interpreter provenance
          │
          ▼
 Python command dispatcher
  ├── Makefile      ← canonical human-facing interface
  └── project.sh    ← Bash adapter
```

A shell-global `uv` may exist and may even win normal `PATH` resolution. That is observable, but project targets deliberately avoid depending on it.

## First use

1. Create/activate the Conda environment you want to own the project's Python version.
2. Run `make doctor`.
3. Run `make setup`.
4. Run `make check`.

Typical lifecycle:

```text
make doctor
make setup
make test
make lint
make check
```

From Bash, the equivalent adapter is available:

```bash
./project.sh doctor
./project.sh setup
./project.sh test
./project.sh lint
./project.sh check
```

This includes Linux/macOS Bash, WSL, and Git Bash/MSYS2 on Windows when their normal Conda activation is available. The Bash adapter delegates to the same Python command dispatcher as Make, so it does not maintain a second implementation of project behavior.

Use `make help` or `./project.sh help` for the complete command list.

## Environment observability

`make doctor` reports:

- host platform, shell environment, Bash availability/version, GNU Make availability/version, and the Bash adapter path;
- active Python and version;
- Conda activation/prefix and whether Python is actually inside it;
- the `uv` selected by shell `PATH`;
- every visible `uv` executable found on `PATH`;
- the Conda-local `uv` used by the project;
- `.venv` existence, Python version, base prefix and provenance metadata;
- repository Python policy (`.python-version`, `requires-python`, authority);
- effective Python resolution policy used for `uv`;
- color/theme configuration;
- bootstrap requirements, warnings, errors and a final environment-contract verdict.

Color is controlled by:

- `config/console-colors.json`
- `config/doctor-theme.json`

Useful variants:

```text
make doctor
make doctor-no-color
make doctor-force-color
```

## Repository layout

```text
.
├── AGENTS.md
├── CLAUDE.md
├── PROJECT.md
├── README.md
├── Makefile
├── project.sh
├── pyproject.toml
├── config/
│   ├── console-colors.json
│   └── doctor-theme.json
├── scripts/
│   ├── _console.py
│   ├── bootstrap.py
│   ├── doctor.py
│   ├── repo.py
│   └── agents_check.py
├── src/project_name/
├── tests/
├── notebooks/
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── reference/
├── docs/
│   ├── architecture/
│   └── adr/
├── ai/
│   ├── agents/
│   └── skills/
├── .github/
│   ├── agents/
│   └── skills/
├── .agents/
├── .codex/
└── .claude/
```

## Command interface policy

The Makefile is the canonical human-facing interface. `project.sh` is a supported Bash adapter exposing the same command names for environments where a shell-native entry point is useful. Both are intentionally thin and delegate to `scripts/repo.py`; environment/bootstrap logic is not duplicated in shell code.

For humans and coding agents, recurring repository operations belong behind the stable project command surface. Direct tool commands are implementation details unless debugging the command layer itself.

Important targets:

| Target | Purpose |
|---|---|
| `make doctor` | Inspect environment state and policy. |
| `make bootstrap` | Install/update Conda-local `uv`; create `.venv`; write provenance. |
| `make sync` | Synchronize dependencies into `.venv`. |
| `make setup` | Bootstrap, sync and diagnose. |
| `make env-rebuild` | Recreate `.venv` from the currently active Conda Python. |
| `make lock` | Refresh `uv.lock`. |
| `make test` | Run tests. |
| `make lint` | Run static checks. |
| `make format` | Format/fix supported files. |
| `make check` | Run quality gates plus agent/skill validation. |
| `make agents-check` | Validate AI policy scaffold. |

Every target above can also be called from Bash as `./project.sh <command>`, for example `./project.sh doctor` or `./project.sh env-rebuild`.

## Python source vs notebooks

Use notebooks for exploration, investigation and visual experimentation. Move logic that must be repeatable, testable or callable into `.py` modules/scripts and expose recurring execution through the Makefile.

## Agent/skill architecture

The canonical reusable AI instructions live under `ai/`:

```text
repository policy
      │
      ▼
  AGENTS.md
      │
      ├── specialized agents  -> ai/agents/
      └── reusable skills     -> ai/skills/
               │
               ▼
       tool-specific adapters
       .github / .agents / .codex / .claude
```

The adapters are intentionally lightweight. They point tools toward the same canonical instructions instead of maintaining divergent copies.

Run:

```text
make agents-list
make skills-list
make agents-check
```

## Instantiating the template

At minimum, replace:

- `project-template` in `pyproject.toml`;
- `src/project_name/` with the real import package;
- the package name used by `make run` in `scripts/repo.py`;
- project identity/scope in `PROJECT.md`;
- this README title/description.

Keep the environment contract unless the new repository intentionally adopts a different Python authority model.
