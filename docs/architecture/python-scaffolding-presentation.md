---
marp: true
title: Python Scaffolding
description: Architecture, concepts, structure, workflow, and evolution strategy
paginate: true
---

# Python Scaffolding

## A reproducible development foundation for Python projects

**Environment architecture · Makefile contract · uv/Conda flexibility · diagnostics · CI · preservation**

---

# 1. What the project is

Python Scaffolding is not merely a template repository.

It is a **development contract** that standardizes how a Python project is:

- bootstrapped;
- diagnosed;
- executed;
- tested;
- validated;
- reproduced;
- evolved;
- preserved.

The central idea is simple:

> **Users interact with the project through stable commands while the environment implementation remains replaceable.**

---

# 2. Core design idea

```mermaid
flowchart TD
    U[Developer / CI / Automation]
    M[Makefile contract]
    P[Project commands]
    E[Environment policy]
    R[Runtime and tooling]
    C[Source code]
    T[Tests]
    D[Diagnostics]

    U --> M
    M --> P
    P --> E
    E --> R
    P --> C
    P --> T
    P --> D
```

The **Makefile is the public interface**.

Everything beneath it may evolve without forcing the developer to relearn the project.

---

# 3. Why scaffolding matters

A project often fails operationally long before its application logic fails.

Typical causes include:

- wrong Python interpreter;
- stale virtual environments;
- PATH ambiguity;
- hidden machine assumptions;
- drift between Windows, Linux, CI, and developer machines;
- bootstrap scripts that duplicate logic;
- tool installation that cannot be reproduced;
- commands that work only because the developer remembers the correct sequence.

The scaffolding exists to make those assumptions **explicit, inspectable, testable, and replaceable**.

---

# 4. Design principles

```mermaid
mindmap
  root((Python Scaffolding))
    Stable Interface
      Makefile-first
      Predictable commands
      Minimal cognitive overhead
    Reproducibility
      Locked dependencies
      Provenance checks
      CI parity
    Environment Awareness
      Interpreter identity
      Conda state
      uv state
      virtualenv state
    Separation of Concerns
      Bootstrap
      Policy
      Diagnostics
      Application
    Portability
      Windows
      Linux
      Future native uv
    Preservation
      Git history
      Phased evolution
      Tagged baselines
      Release artifacts
```

---

# 5. The public contract

The developer should not need to remember which low-level tool performs each action.

The expected interaction looks like this:

```text
make doctor
make setup
make sync
make check
make test
make run
make clean
```

The implementation behind those commands may change.

The contract should not.

---

# 6. Makefile-first architecture

```mermaid
flowchart LR
    DEV[Developer]
    CI[CI runner]
    AGENT[Automation / AI agent]

    MAKE[Makefile]

    BOOT[Bootstrap]
    DOC[Doctor]
    TEST[Test / lint]
    RUN[Run]
    CLEAN[Clean]
    BUILD[Build / package]

    DEV --> MAKE
    CI --> MAKE
    AGENT --> MAKE

    MAKE --> BOOT
    MAKE --> DOC
    MAKE --> TEST
    MAKE --> RUN
    MAKE --> CLEAN
    MAKE --> BUILD
```

The Makefile acts as an **anti-fragmentation layer**.

Humans, CI, and automation invoke the same contract.

---

# 7. Environment architecture

One of the major architectural shifts was to stop treating environment handling as scattered shell logic.

Instead, environment behavior becomes a defined subsystem.

```mermaid
flowchart TD
    CFG[environment.toml]
    ENV[environment.py]
    PS[project.ps1]
    SH[project.sh]
    MK[Makefile]
    DOC[doctor]
    UV[uv]
    CONDA[Conda]
    PY[Python]
    VENV[.venv]

    CFG --> ENV
    ENV --> DOC

    MK --> PS
    MK --> SH
    PS --> ENV
    SH --> ENV

    ENV --> UV
    ENV --> CONDA
    ENV --> PY
    ENV --> VENV
```

The shell wrappers stay thin.

The policy stays centralized.

---

# 8. Environment authority

The scaffolding separates **environment policy** from **environment implementation**.

This makes multiple strategies possible.

```mermaid
flowchart LR
    CONTRACT[Project contract]
    POLICY[Environment policy]

    CONDAUV[Conda + uv]
    UVONLY[Native uv]
    FUTURE[Future provider]

    CONTRACT --> POLICY

    POLICY --> CONDAUV
    POLICY --> UVONLY
    POLICY --> FUTURE
```

This is the important architectural point:

> The project does not become a “Conda project” or a “uv project”.  
> It becomes a project with a stable environment contract.

---

# 9. Conda + uv mode

The original practical model is intentionally hybrid.

```mermaid
flowchart TD
    CONDA[Conda]
    PYVER[Python version selection]
    UV[uv]
    DEPS[Dependency resolution]
    LOCK[uv.lock]
    VENV[Project .venv]
    APP[Application]

    CONDA --> PYVER
    PYVER --> UV
    UV --> DEPS
    DEPS --> LOCK
    UV --> VENV
    VENV --> APP
```

### Responsibility split

- **Conda**: Python version / host environment selection.
- **uv**: project dependencies, locking, synchronization, execution.
- **Makefile**: stable interface.
- **Doctor**: verifies that the selected layers are actually the ones in use.

---

# 10. Native uv mode

Phase 4 introduced the architectural ability to support **uv as authority**.

```mermaid
flowchart TD
    UV[uv]
    PY[uv-managed Python]
    VENV[.venv]
    LOCK[uv.lock]
    PROJECT[Project]
    MAKE[Makefile contract]

    MAKE --> UV
    UV --> PY
    UV --> VENV
    UV --> LOCK
    VENV --> PROJECT
```

The objective is not merely to “use uv”.

The objective is to prove that **changing the environment authority does not break the project contract**.

---

# 11. Doctor as an architectural component

`doctor` is not just a convenience command.

It is the project’s **environment observability layer**.

```mermaid
flowchart TD
    DOC[make doctor]

    PY[Python executable + version]
    CONDA[Conda activation]
    UV[uv executable + version]
    PATH[PATH provenance]
    VENV[Virtual environment]
    CFG[Project policy]
    KERNEL[Jupyter kernel]
    WARN[Warnings / invariant violations]

    DOC --> PY
    DOC --> CONDA
    DOC --> UV
    DOC --> PATH
    DOC --> VENV
    DOC --> CFG
    DOC --> KERNEL

    PY --> WARN
    CONDA --> WARN
    UV --> WARN
    PATH --> WARN
    VENV --> WARN
    CFG --> WARN
```

The goal is **provenance**, not merely availability.

“Python exists” is weaker than:

> “This exact Python executable is the one the project expects.”

---

# 12. Bootstrap boundary

Bootstrap logic must remain intentionally small.

```mermaid
flowchart TD
    USER[Fresh machine / repository clone]
    WRAPPER[project.ps1 / project.sh]
    MIN[Minimal pre-Python checks]
    PY[Python available]
    ENV[Environment subsystem]
    FULL[Full doctor / setup]

    USER --> WRAPPER
    WRAPPER --> MIN
    MIN --> PY
    PY --> ENV
    ENV --> FULL
```

This prevents the classic bootstrap paradox:

> A Python diagnostic cannot diagnose why Python itself is unavailable.

---

# 13. Proposed repository structure

```mermaid
flowchart TD
    ROOT[python_scaffolding/]

    ROOT --> MAKE[Makefile]
    ROOT --> PYPROJECT[pyproject.toml]
    ROOT --> LOCK[uv.lock]
    ROOT --> ENVIRONMENT[environment.toml]

    ROOT --> SRC[src/]
    ROOT --> TESTS[tests/]
    ROOT --> SCRIPTS[scripts/]
    ROOT --> DOCS[docs/]
    ROOT --> CI[.github/workflows/]
    ROOT --> AGENTS[agents / skills hooks]
    ROOT --> PS[project.ps1]
    ROOT --> SH[project.sh]

    SCRIPTS --> ENV[environment.py]
    SCRIPTS --> DOCTOR[doctor logic]

    TESTS --> UNIT[unit tests]
    TESTS --> INTEGRATION[integration tests]

    DOCS --> ARCH[architecture]
    DOCS --> DECISIONS[decisions / reports]
    DOCS --> RELEASES[phase archaeology]
```

---

# 14. Separation of responsibilities

```mermaid
flowchart LR
    UI[Makefile]
    BOOT[Bootstrap wrappers]
    POLICY[Environment policy]
    IMPLEMENTATION[Environment implementation]
    APP[Application code]
    VERIFY[Tests + CI]
    DOCS[Documentation]

    UI --> BOOT
    UI --> POLICY
    POLICY --> IMPLEMENTATION

    UI --> APP
    UI --> VERIFY

    POLICY --> VERIFY
    IMPLEMENTATION --> VERIFY

    DOCS -. explains .-> UI
    DOCS -. explains .-> POLICY
```

Each layer should have a narrow reason to change.

That reduces accidental coupling.

---

# 15. Phase 0 — Repair the invariants

The first phase fixed the foundation before adding new abstractions.

Key goals included:

- repair license inconsistency;
- repair agent references / validator behavior;
- commit `uv.lock`;
- repair `clean`;
- declare actual Python compatibility;
- verify environment-sensitive command provenance.

```mermaid
flowchart LR
    BROKEN[Implicit / inconsistent invariants]
    REPAIR[Phase 0 repairs]
    BASELINE[Trustworthy baseline]

    BROKEN --> REPAIR --> BASELINE
```

---

# 16. Phase 1 — Extract the architecture

Phase 1 moved environment behavior from scattered implementation details into explicit architecture.

```mermaid
flowchart LR
    BEFORE[Hard-coded environment logic]
    CFG[environment.toml]
    CORE[shared environment.py]
    AFTER[Centralized environment policy]

    BEFORE --> CFG
    BEFORE --> CORE

    CFG --> AFTER
    CORE --> AFTER
```

This was the transition from **scripts that happen to work** to **an environment subsystem**.

---

# 17. Phase 2 — Fix bootstrap boundaries

Phase 2 established a clear boundary between:

- shell/bootstrap responsibilities;
- Python diagnostics;
- project logic.

```mermaid
flowchart LR
    SHELL[Shell / PowerShell]
    PRE[Minimal preflight]
    PY[Python layer]
    DOCTOR[Full doctor]
    PROJECT[Project commands]

    SHELL --> PRE --> PY --> DOCTOR --> PROJECT
```

Thin wrappers remain disposable.

The Python implementation remains authoritative.

---

# 18. Phase 3 — Test the scaffold itself

The scaffold must be treated as production code.

```mermaid
flowchart TD
    CODE[Scaffolding code]
    UNIT[Environment unit tests]
    INTEGRATION[Command integration tests]
    WIN[Windows CI]
    LINUX[Linux CI]
    CONTRACT[Validated project contract]

    CODE --> UNIT
    CODE --> INTEGRATION

    UNIT --> WIN
    UNIT --> LINUX
    INTEGRATION --> WIN
    INTEGRATION --> LINUX

    WIN --> CONTRACT
    LINUX --> CONTRACT
```

The goal is not only to test applications created from the scaffold.

The scaffold itself must prove that it still behaves correctly.

---

# 19. Phase 4 — Pluggable environment authority

Phase 4 proves the architectural abstraction.

```mermaid
flowchart TD
    CONTRACT[Stable Makefile contract]
    POLICY[Shared environment contract]

    MODE1[authority = conda + uv]
    MODE2[authority = uv]

    SAME[Same developer workflow]

    CONTRACT --> POLICY
    POLICY --> MODE1
    POLICY --> MODE2

    MODE1 --> SAME
    MODE2 --> SAME
```

If both modes satisfy the same contract, the abstraction is doing useful work.

---

# 20. Git workflow and software archaeology

The repository treats history as engineering evidence.

```mermaid
gitGraph
    commit id: "baseline"
    branch dev
    checkout dev

    branch feature-phase
    checkout feature-phase
    commit id: "implementation"
    commit id: "tests"
    commit id: "docs"

    checkout dev
    merge feature-phase id: "merge phase"

    checkout main
    merge dev id: "release"
    commit tag: "vX.Y.Z"

    branch hotfix
    checkout hotfix
    commit id: "production fix"

    checkout main
    merge hotfix id: "hotfix release"

    checkout dev
    merge main id: "propagate fix"
```

Important principles:

- avoid squash merges when preserving implementation history matters;
- keep phase boundaries visible;
- tag releases semantically;
- document hotfixes;
- keep release artifacts for later archaeology.

---

# 21. Releases as historical checkpoints

A release represents more than a binary version.

It captures:

```mermaid
flowchart TD
    REL[Release]
    TAG[Semantic tag]
    NOTES[Phase summary]
    FIX[Hotfix context]
    ART[Artifacts]
    REPORT[Detailed report]
    HASH[Checksums]
    HISTORY[Repository history]

    REL --> TAG
    REL --> NOTES
    REL --> FIX
    REL --> ART
    REL --> REPORT
    REL --> HASH

    TAG --> HISTORY
    NOTES --> HISTORY
    ART --> HISTORY
    REPORT --> HISTORY
```

This supports future reconstruction of **what changed, why it changed, and how it behaved**.

---

# 22. Minimal AI / agent integration

The scaffolding may support AI-assisted development without becoming an agent framework itself.

```mermaid
flowchart LR
    SCAFFOLD[Python Scaffolding]
    HOOKS[Minimal agent / skill hooks]
    CODEX[Codex]
    CLAUDE[Claude Code]
    FUTURE[Other tools]

    SCAFFOLD --> HOOKS
    HOOKS --> CODEX
    HOOKS --> CLAUDE
    HOOKS --> FUTURE
```

The principle is:

> Keep only the canonical integration surface here.  
> Evolve rich agent architecture elsewhere.

This prevents the scaffolding from becoming overloaded with unrelated responsibilities.

---

# 23. What the scaffold should generate

A future mature scaffold can produce a project with the same contract regardless of application type.

```mermaid
flowchart TD
    TEMPLATE[Scaffolding]
    CLI[CLI application]
    API[API service]
    DATA[Data project]
    ML[ML / analytics]
    NOTEBOOK[Notebook-heavy project]
    AUTOMATION[Automation]
    LIB[Python library]

    TEMPLATE --> CLI
    TEMPLATE --> API
    TEMPLATE --> DATA
    TEMPLATE --> ML
    TEMPLATE --> NOTEBOOK
    TEMPLATE --> AUTOMATION
    TEMPLATE --> LIB
```

The scaffold standardizes **engineering mechanics**, not business logic.

---

# 24. Project invariants

A good invariant is a rule the project can verify.

```mermaid
flowchart LR
    INV[Project invariants]

    INV --> I1[Commands go through Makefile]
    INV --> I2[Dependencies are locked]
    INV --> I3[Interpreter provenance is known]
    INV --> I4[Environment policy is centralized]
    INV --> I5[CI uses public project commands]
    INV --> I6[Bootstrap wrappers stay thin]
    INV --> I7[History is preserved]
    INV --> I8[Platform differences are explicit]
```

These invariants turn convention into architecture.

---

# 25. Desired developer experience

```mermaid
sequenceDiagram
    participant D as Developer
    participant M as Makefile
    participant E as Environment layer
    participant U as uv / runtime
    participant C as Codebase

    D->>M: make doctor
    M->>E: inspect environment
    E-->>D: provenance + warnings

    D->>M: make setup
    M->>E: resolve policy
    E->>U: create/sync environment
    U-->>E: ready

    D->>M: make check
    M->>C: lint + test + validate
    C-->>D: project status
```

The user interacts with **intent**, not implementation detail.

---

# 26. Architectural philosophy

The scaffold follows several broader software-engineering ideas:

- **Ports and adapters** — the Makefile is a stable entry point while environment providers are replaceable.
- **Dependency inversion** — workflow depends on an environment contract, not directly on Conda or uv.
- **Observability** — `doctor` exposes state and provenance.
- **Reproducibility** — lockfiles, CI, and deterministic commands reduce hidden state.
- **Separation of concerns** — bootstrap, environment policy, diagnostics, application code, and CI remain distinct.
- **Evolutionary architecture** — the system is designed to change providers without rewriting the user workflow.

---

# 27. The scaffold as a platform

```mermaid
flowchart TD
    FOUNDATION[Python Scaffolding]

    ENV[Environment contract]
    EXEC[Execution contract]
    TEST[Testing contract]
    OBS[Diagnostics]
    CI[CI contract]
    DOC[Documentation]
    HIST[Historical preservation]

    FOUNDATION --> ENV
    FOUNDATION --> EXEC
    FOUNDATION --> TEST
    FOUNDATION --> OBS
    FOUNDATION --> CI
    FOUNDATION --> DOC
    FOUNDATION --> HIST

    ENV --> PROJECTS[Future projects]
    EXEC --> PROJECTS
    TEST --> PROJECTS
    OBS --> PROJECTS
    CI --> PROJECTS
```

This is why it is better understood as a **small development platform** than as a template.

---

# 28. Evolution path

```mermaid
flowchart LR
    V1[Working personal scaffold]
    V2[Explicit environment architecture]
    V3[Cross-platform validation]
    V4[Pluggable environment authority]
    V5[Template generation]
    V6[Reusable organization standard]

    V1 --> V2 --> V3 --> V4 --> V5 --> V6
```

The important rule is to evolve only after the previous layer becomes trustworthy.

Architecture should emerge from proven constraints—not from abstraction for its own sake.

---

# 29. What should remain intentionally simple

```mermaid
mindmap
  root((Keep simple))
    Makefile
      Few canonical targets
      Stable naming
    Wrappers
      Thin PowerShell
      Thin Bash
    Configuration
      Explicit
      Human-readable
    Agent support
      Hooks only
      No platform explosion
    Bootstrap
      Minimum logic
      No duplicated policy
```

A scaffold becomes dangerous when the scaffold itself is harder to understand than the projects it creates.

---

# 30. The central architectural loop

```mermaid
flowchart LR
    DEFINE[Define invariant]
    IMPLEMENT[Implement once]
    EXPOSE[Expose through Makefile]
    OBSERVE[Inspect with doctor]
    TEST[Test locally + CI]
    FREEZE[Tag / release / document]
    EVOLVE[Evolve architecture]

    DEFINE --> IMPLEMENT
    IMPLEMENT --> EXPOSE
    EXPOSE --> OBSERVE
    OBSERVE --> TEST
    TEST --> FREEZE
    FREEZE --> EVOLVE
    EVOLVE --> DEFINE
```

This loop captures the project’s engineering philosophy.

---

# 31. Final view

```mermaid
flowchart TD
    USER[Developer]
    CONTRACT[Stable Makefile interface]

    ENV[Environment architecture]
    DIAG[Doctor / provenance]
    TESTS[Tests]
    CI[CI]
    APP[Application code]
    DOCS[Documentation]
    HISTORY[Git + releases]

    USER --> CONTRACT

    CONTRACT --> ENV
    CONTRACT --> DIAG
    CONTRACT --> TESTS
    CONTRACT --> APP

    ENV --> CI
    TESTS --> CI

    ENV --> DOCS
    DIAG --> DOCS
    TESTS --> DOCS

    DOCS --> HISTORY
    CI --> HISTORY
```

## Python Scaffolding

**A reproducible, inspectable, evolvable development contract.**

Not just a place to start a Python project.

A way to make projects behave predictably as they grow.