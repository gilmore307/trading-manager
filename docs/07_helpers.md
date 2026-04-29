# Helpers

## Purpose

`trading-main` owns shared helper code for trading-wide infrastructure concerns that multiple component repositories may consume.

The earlier docs stay project-wide:

- `00_scope.md` through `06_memory.md` describe the whole trading platform repository and its governance.
- This file describes the shared helper source boundary under `src/` specifically.

Helpers exist to keep repeated cross-repository mechanics consistent without turning `trading-main` into a runtime implementation repository.

## What Helpers Own

Shared helpers may own reusable infrastructure behavior such as:

- registry reading and validation helpers;
- secret-alias resolution helpers that never store secret values;
- artifact reference helpers;
- manifest formatting or validation helpers;
- request and ready-signal helper utilities;
- shared schema or field validation utilities;
- small CLI or library utilities that support platform contracts.

Helpers must not own:

- component runtime implementations;
- market data fetching;
- strategy logic;
- model training or inference logic;
- live/paper execution daemons;
- dashboard application behavior;
- generated data, notebooks, logs, or artifacts;
- secrets, credentials, broker keys, or exchange keys.

## Directory Layout

```text
src/
  README.md                 Source boundary summary.
  trading_scripts/         Formal Python registry helper package source.
scripts/
  apply_registry_migrations.py  Executable registry maintenance command.
tests/
  README.md                 Test boundary and inventory.
  test_trading_registry.py  Python helper and registry governance tests.
```

Python helper packages live under `src/` with root package metadata in `pyproject.toml`. Executable maintenance or operational entrypoints live under `scripts/` and may import `src/`; `src/` must not import `scripts/`. Tests live under `tests/` and must be inventoried in `tests/README.md`. Future helper packages should use a named package/subdirectory with a clear README when the boundary is more than trivial.

## Current Package Status

The formal cross-repository helper runtime surface is now Python.

Current package facts:

- Package metadata lives in root `pyproject.toml`.
- Python package name: `trading-main-helpers`.
- Import package: `trading_registry`.
- Requires Python 3.12 or newer.
- Shared environment install command:

  ```bash
  /root/projects/trading-main/.venv/bin/python -m pip install -r /root/projects/trading-main/requirements.txt
  /root/projects/trading-main/.venv/bin/python -m pip install -e /root/projects/trading-main
  ```

- Python helper test command:

  ```bash
  PYTHONPATH=src python3 -m unittest discover -s tests
  ```

Component repositories should consume the Python package.

Registry `script` rows may record approved helper export surfaces and source paths, but they are not package installation contracts by themselves.

## Public Interface Rules

Shared helper APIs must be explicit and stable enough for component repositories to depend on.

Rules:

- Keep public exports narrow.
- Prefer stable registry ids over renameable labels where helpers touch registry entries.
- Do not introduce key-input registry helper APIs.
- Keep helper behavior generic to the trading platform.
- Avoid local-only paths unless the path is an approved registry entry or documented environment anchor.
- Keep secrets outside the repository; helpers may resolve aliases but must not store secret values.
- Add tests when behavior becomes executable rather than documentation-only.

## Registry Helpers

Current official Python registry item lookup and secret helper surface is id-input only:

- `RegistryReader.get_key_by_id(id)`
- `RegistryReader.get_payload_by_id(id)`
- `RegistryReader.get_path_by_id(id)`
- `SecretResolver.load_secret_text_by_config_id(config_id, field_name=None)`

Registry kind and payload-format vocabularies are scripts/schema concerns, not runtime helper exports. Tests compare kind files and payload-format rows with SQL constraints; do not add package-level vocabulary validator helpers unless runtime validation becomes a real consumer requirement.

Source secret configs should point to one source-level JSON file per provider/source. The secret resolver can return either the raw JSON text or one named JSON string field.

The official Python helper source lives under `src/trading_scripts/`.

Registry maintenance commands, such as regenerating `scripts/current.csv`, are registry operations. They may be referenced by helpers, but their operating guide lives in `docs/08_registry.md`.

## Recording Duty

When any component work discovers or creates a helper that should be global, record it in `trading-main` instead of leaving it in the component repository.

- Shared helper code belongs under `src/`.
- Public helper surfaces that automation may call should be registered as `script` rows when stable.
- Test scripts are not registry `script` rows; document each test script in its test-directory README instead.
- Helper-facing fields, config keys, statuses, and type values must be routed through the registry before cross-repository use.
- Temporary helper names from implementation work must be reported during review if they may become shared.

## Acceptance Checklist

A helper change is acceptable when:

- the helper remains shared infrastructure, not component runtime code;
- public API shape is documented or obvious from tests;
- distribution status is explicit: Python package for runtime dependency or internal-only maintenance helper;
- packaged helpers declare runtime version, version policy, install method, and import/call examples;
- relevant tests pass;
- every first-party test script is documented in the owning test-directory README;
- no secrets or credentials are stored;
- helper behavior does not duplicate component-owned logic;
- registry item lookup helpers use id-based lookup only;
- affected registry, template, or workflow docs are updated when helper behavior encodes a shared convention.


## Brave Search helper

Use `trading_web_search.brave` for code-level web search. The helper resolves `cfg_BRAVESEARCH` / `BRAVE_SEARCH_SECRET_ALIAS` through the trading registry and local `/root/secrets/brave.json`; repo code must not embed API keys.

Default usage:

```python
from trading_web_search import brave_search

results = brave_search("site:bls.gov CPI release schedule", count=5)
```

Production pipelines should treat search as discovery only: accept official source domains before parsing or persisting discovered calendar URLs.
