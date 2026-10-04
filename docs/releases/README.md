# Release archaeology

The repository uses SemVer tags both as release identifiers and as software-archaeology markers for the completed scaffold roadmap.

| Version | Boundary | Meaning | Full report |
|---|---|---|---|
| `v0.1.0` | `046632d` | Phase 0 — repair current invariants | `v0.1.0-full-report.md` |
| `v0.2.0` | `a744e5d` | Phase 1 — extract environment architecture | `v0.2.0-full-report.md` |
| `v0.3.0` | `a515354` | Phase 2 — bootstrap boundaries | `v0.3.0-full-report.md` |
| `v0.4.0` | `5b4acf8` | Phase 3 — scaffold testing and cross-platform CI | `v0.4.0-full-report.md` |
| `v0.5.0` | `5ce2357` | Phase 4 — dual Python authority / uv default | `v0.5.0-full-report.md` |
| `v0.5.1` | `0d9e591` | Windows `env-rebuild` hotfix | `v0.5.1-full-report.md` |
| `v1.0.0` | `d03d413` | first stable scaffold baseline | `v1.0.0-full-report.md` |

The historical versions intentionally use the `0.x` line because they represent architecture under active construction. The Windows correction is a patch on the Phase 4 baseline. `v1.0.0` is the first point explicitly promoted and published as the stable public scaffold contract.

Each release page keeps a concise phase summary. Each comprehensive Markdown report is both committed under `docs/releases/` and attached to its matching GitHub release so the history remains readable even when browsing tags independently.

The `v0.5.1` report is intentionally a postmortem-style artifact. It preserves the original Windows self-delete failure, the first process-replacement fix, the PowerShell prompt/output race discovered only on Pangaea, and the final foreground-parent correction.
