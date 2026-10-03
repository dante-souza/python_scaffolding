# Dual-Authority Lifecycle

## Phase 4D responsibility

Phase 4D carries the authority model beyond bootstrap into the normal repository
lifecycle while preserving one public command surface:

```text
                  Makefile
                     |
                     v
               scripts/repo.py
                 /         \
                /           \
       authority=conda     authority=uv
              |                |
     active Conda Python     native uv
              |                |
       python -m uv        managed Python
                \           /
                 \         /
                  project .venv
                     |
              test / lint / run
```

The Makefile target names do not change between modes.

## Dispatcher rule

Conda and native uv deliberately do **not** use identical dispatcher mechanics.

### Conda authority

Conda is active shell state. If the dispatcher starts under a Python outside the
active Conda prefix, it re-executes itself under the Conda interpreter before a
policy-sensitive command continues. This preserves the established
`python -m uv` ownership contract.

### Native uv authority

Native uv has no analogous "active environment" that the dispatcher should
pretend exists. The dispatcher therefore does not re-exec itself merely because
the configured authority is `uv`.

Instead it explicitly resolves:

1. the native `uv` executable from `PATH`;
2. the configured uv-managed Python;
3. the concrete managed-Python version.

Lifecycle commands then pass those resolved paths explicitly.

This distinction is intentional rather than an implementation shortcut.

## sync and lock

The same targets now dispatch differently behind the shared interface:

```text
make sync

conda -> <conda-python> -m uv sync --python <project-venv-python>
uv    -> <uv> sync --python <project-venv-python>


make lock

conda -> <conda-python> -m uv lock --python <conda-python>
uv    -> <uv> lock --python <uv-managed-python>
```

Both modes validate `.venv` provenance against their configured authority
before project execution commands continue.

## Doctor

`make doctor` now reports authority-neutral fields plus authority-specific
evidence.

For Conda it checks the active prefix, current interpreter membership, and
Conda-local uv.

For native uv it checks the native uv executable and resolves the configured
managed Python without treating Conda activation as a requirement.

A missing uv-managed Python is a bootstrap condition, not evidence that the
host's arbitrary bootstrap Python is invalid.

## Boundary after 4D

At this point policy, discovery, bootstrap, provenance, dispatcher, dependency
sync/lock, and diagnostics all understand both authority modes.

The repository still defaults to `authority = "conda"`. The remaining Phase 4
work is to prove the same Makefile contract end-to-end under both modes,
including CI coverage, before deciding whether the default should change.
