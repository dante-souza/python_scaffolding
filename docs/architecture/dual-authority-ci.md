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

Phase 4E passes only when Linux/Windows under both Conda and uv are green.
