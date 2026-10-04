# Dual-Authority CI Proof

## Goal

Phase 4E proves that Python-authority choice remains an implementation detail
behind one stable Makefile interface.

## Matrix

```text
                 authority
              conda       uv
            +----------+----------+
Linux       | make     | make     |
            | setup    | setup    |
            | check    | check    |
            +----------+----------+
Windows     | make     | make     |
            | setup    | setup    |
            | check    | check    |
            +----------+----------+
```

All four lanes run from the same commit and use the same project commands.

## Default

Phase 4E changes the reusable scaffold default to:

```toml
[environment]
authority = "uv"
```

Projects that deliberately want Conda to select Python change only that policy
value to `"conda"`; the public Makefile workflow remains unchanged.

## CI boundary

Runner preparation may differ:

- Conda lanes activate Conda and select `authority = "conda"` in the ephemeral
  checkout.
- uv lanes install a native uv executable.
- Windows lanes install GNU Make.

After runner preparation, every lane executes only:

```text
make setup
make check
```

Phase 4E is accepted only when Linux/Windows under both Conda and uv are green. The final matrix satisfied that condition.

The first native-uv matrix run also exposed an important provenance regression: once `.venv` existed, authority discovery could resolve the project environment instead of the uv-managed source Python. The corrective invariant is now explicit: managed-Python authority discovery uses `--system`, and tests guard that behavior on both platforms.
