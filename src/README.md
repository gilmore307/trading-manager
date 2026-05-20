# Source

`src/` contains importable Python packages owned by `trading-manager`.

## Boundary

- `src/` owns reusable implementation modules.
- `scripts/` owns executable entrypoints and may import `src/`.
- `src/` must not import `scripts/`.
- Component-specific runtime logic belongs in the component repositories.

## Packages

| Package | Role |
|---|---|
| `trading_registry` | Registry reader and secret-alias resolver. |
| `trading_manager_tasks` | Request, receipt, scheduler, evidence, review, and status helpers. |
| `trading_web_search` | Web-search helper wrapper. |
| `trading_bigquery` | Dependency-light BigQuery REST helper using registry secret aliases. |

## Install

```bash
/root/projects/trading-manager/.venv/bin/python -m pip install -r /root/projects/trading-manager/requirements.txt
/root/projects/trading-manager/.venv/bin/python -m pip install -e /root/projects/trading-manager
```

## Verify

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
python3 -m compileall -q src scripts
```

## Rules

- Keep helper APIs id/input oriented where registry stability matters.
- Do not hard-code secret values.
- Do not place executable wrappers here.
- Do not place generated artifacts, logs, caches, or provider payloads here.
