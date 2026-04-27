# Source

`src/` stores importable, reusable implementation code for `trading-main` shared helper packages.

The formal cross-repository helper runtime surface is Python. Package metadata lives in root `pyproject.toml`; importable source lives under this directory.

## Layout

```text
src/
  README.md
  trading_registry/   Python registry reader and secret-resolution package.
```

Tests live under `tests/`. Executable maintenance entrypoints live under `scripts/`.

## Install

From the shared environment:

```bash
/root/projects/trading-main/.venv/bin/python -m pip install -r /root/projects/trading-main/requirements.txt
/root/projects/trading-main/.venv/bin/python -m pip install -e /root/projects/trading-main
```

## Test

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Allowed Here

- generic SQL helpers;
- artifact path/reference helpers;
- manifest helpers;
- request and ready-signal helpers;
- shared validation utilities;
- reusable Python packages consumed by component repositories.

## Not Allowed Here

- executable maintenance wrappers or one-off operational commands;
- component runtime implementations;
- broker/exchange trading daemons;
- strategy logic;
- model training logic;
- dashboard application code;
- secrets or credentials.

Use `scripts/` for executable commands. `scripts/` may import `src/`; `src/` must not import `scripts/`.

See `../docs/07_helpers.md` for the docs-level helper operating guide.
