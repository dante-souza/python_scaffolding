# Release archaeology

The repository uses SemVer tags both as release identifiers and as software-archaeology markers for the completed scaffold roadmap.

| Version | Boundary | Meaning |
|---|---|---|
| `v0.1.0` | `046632d` | Phase 0 — repair current invariants |
| `v0.2.0` | `a744e5d` | Phase 1 — extract environment architecture |
| `v0.3.0` | `a515354` | Phase 2 — bootstrap boundaries |
| `v0.4.0` | `5b4acf8` | Phase 3 — scaffold testing and cross-platform CI |
| `v0.5.0` | `5ce2357` | Phase 4 — dual Python authority / uv default |
| `v0.5.1` | `0d9e591` | Windows `env-rebuild` hotfix |
| `v1.0.0` | release merge on `main` | first stable scaffold baseline |

The historical versions intentionally use the `0.x` line because they represent architecture under active construction. The Windows correction is a patch on the Phase 4 baseline. `v1.0.0` is the first point explicitly promoted and published as the stable public scaffold contract.

The full release/postmortem report is `v1.0.0-full-report.md`.
