# Helpers

`trading-manager` owns shared Python helper packages that support registry access, secret-alias resolution, request/receipt normalization, scheduler planning, and status/report construction.

## Source Boundary

```text
src/trading_registry/        Registry reader and secret resolver.
src/trading_manager_tasks/   Manager task, scheduler, request, receipt, and review helpers.
src/trading_web_search/      Web-search helper wrapper.
src/trading_bigquery/        Dependency-light BigQuery REST helper.
```

## Rules

- `src/` contains importable packages only.
- `scripts/` contains executable entrypoints and may import `src/`.
- `src/` must not import `scripts/`.
- Stable automation-facing commands are scripts and should be registered as `kind=script` when needed.
- Shared helpers must stay generic; component-specific runtime logic belongs in component repositories.
- Secrets are resolved by alias/registry mechanisms, never hard-coded into source or docs.

## Verification

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
python3 -m compileall -q src scripts
```
