# Python Project Base

Reusable repository scaffold for Python projects with a **Makefile-first workflow**, **Bash and PowerShell command adapters**, an explicit environment-policy contract, `.venv` provenance, colorful environment diagnostics, and a shared agent/skill layer. The canonical policy lives in `environment.toml`; both native `uv` and Conda are supported Python authorities, with native `uv` as the default.

The template is intentionally opinionated about **workflow** and explicit about compatibility: `requires-python = ">=3.11"` records the runtime floor required by the scaffold, while `environment.toml` selects the exact Python authority. There is no `.python-version` pin.

## Core contract

```text
                 environment.toml
                  /            \
                 /              \
       authority = uv      authority = conda
              |                   |
      native uv on PATH      active Conda env
              |                   |
      uv-managed Python       Conda Python
               \                 /
                \               /
                 project .venv
                 |            |
        project dependencies  provenance
                 |
          scripts/repo.py
          /      |       \
     Makefile project.sh project.ps1
```

The public Makefile contract is identical in both modes. Conda mode deliberately uses authority-local `python -m uv`; native-uv mode invokes the resolved `uv` executable and managed Python directly.

## First use

The default policy is `authority = "uv"`. Ensure `uv` is available on `PATH`, then:

1. Run `make doctor`.
2. Run `make setup`.
3. Run `make check`.

For Conda-controlled Python selection, change `environment.authority` to `"conda"`, activate the intended Conda environment, and use the same Make targets.

Typical lifecycle:

```text
make doctor
make setup
make test
make lint
make check
```

Shell-native adapters expose the same command vocabulary.

From Bash:

```bash
./project.sh doctor
./project.sh setup
./project.sh test
./project.sh lint
./project.sh check
```

This includes Linux/macOS Bash, WSL, and Git Bash/MSYS2 on Windows; Conda activation is required only when the configured authority is `conda`.

From PowerShell:

```powershell
.\project.ps1 doctor
.\project.ps1 setup
.\project.ps1 test
.\project.ps1 lint
.\project.ps1 check
```

Both adapters delegate to the same Python command dispatcher as Make, so neither maintains a second implementation of project behavior.

If Python cannot be resolved or started, the shell adapter prints minimal pre-Python diagnostics before stopping. Exit code `127` means Python was not found; `126` means it was found but could not be started. WSL requires a Python executable runnable inside WSL rather than a Windows/Cygwin interpreter inherited through `PATH`.

Use `make help`, `./project.sh help`, or `.\project.ps1 help` for the complete command list.

## Environment observability

`make doctor` reports:

- host platform, shell environment, Bash availability/version, GNU Make availability/version, and the Bash adapter path;
- active Python and version;
- configured authority and requested Python version;
- Conda activation/prefix when relevant;
- the `uv` selected by shell `PATH` and every visible `uv` executable;
- the resolved authority Python and authority-specific `uv` invocation used by the project;
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
├── project.ps1
├── pyproject.toml
├── environment.toml
├── config/
│   ├── console-colors.json
│   └── doctor-theme.json
├── scripts/
│   ├── _console.py
│   ├── environment.py
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
│   │   └── bootstrap-boundary.md
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

The Makefile is the canonical human-facing interface. `project.sh` and `project.ps1` are supported Bash and PowerShell adapters exposing the same command names where a shell-native entry point is useful. All three entry points delegate to `scripts/repo.py`; environment/bootstrap logic is not duplicated in shell code. Conda mode may hand execution to the active Conda interpreter before policy-sensitive work; native-uv mode resolves its managed interpreter explicitly without inventing an active-environment concept. `environment.toml` declares environment policy, and `scripts/environment.py` is the single implementation layer that interprets it.

For humans and coding agents, recurring repository operations belong behind the stable project command surface. Direct tool commands are implementation details unless debugging the command layer itself.

Important targets:

| Target | Purpose |
|---|---|
| `make doctor` | Inspect environment state and policy. |
| `make bootstrap` | Prepare the configured Python authority; create `.venv`; write provenance. |
| `make sync` | Synchronize dependencies into `.venv`. |
| `make setup` | Bootstrap, sync and diagnose. |
| `make env-rebuild` | Recreate `.venv` from the configured authority Python. |
| `make lock` | Refresh `uv.lock`. |
| `make test` | Run tests. |
| `make lint` | Run static checks. |
| `make format` | Format/fix supported files. |
| `make check` | Run quality gates plus agent/skill validation. |
| `make agents-check` | Validate AI policy scaffold. |

Every target above can also be called through a shell adapter: Bash uses `./project.sh <command>` and PowerShell uses `.\project.ps1 <command>`.

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


## License

This repository is licensed under the GNU Affero General Public License v3.0. See `LICENSE`.
