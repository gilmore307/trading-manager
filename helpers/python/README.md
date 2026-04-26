# Python Helpers

This directory contains the formal Python helper package for `trading-main`.

Package metadata lives in the repository root `pyproject.toml`.

## Install

From the shared environment:

```bash
/root/projects/trading-main/.venv/bin/python -m pip install -r /root/projects/trading-main/requirements.txt
/root/projects/trading-main/.venv/bin/python -m pip install -e /root/projects/trading-main
```

## Test

```bash
/root/projects/trading-main/.venv/bin/python -m unittest discover -s helpers/python/tests
```

## Packages

- `trading_registry` — id-based registry reader and config-id secret resolver.
