# <bundle-name>

## Purpose

Describe the historical data this bundle acquires and why this bundle boundary exists.

## Source

- Provider/source term:
- Documentation URL:
- Credential config id or no-key rule:
- Official source URL rule, if web/issuer sourced:

## Bundle Boundary

This bundle includes:

- `<data-type-1>`
- `<data-type-2>`

This bundle excludes:

- realtime data;
- execution-time feeds;
- strategy/model decisions;
- durable SQL writes during development.

## Task Key Inputs

Required task key fields:

- `task_id`
- `bundle`
- `params`
- `output_dir`

Optional task key fields:

- `credential_config_id` when the bundle needs a registered credential alias

Put API-specific inputs such as symbols, underlyings, ETF ids, macro release keys, calendar scope, time ranges, snapshot timestamps, granularity, source URLs, and provider parameters inside `params`. Do not put provider documentation URLs in the task key; those belong in registry/provider docs or this README.

## Pipeline Module

Default implementation should start as one `pipeline.py` file with one public `run(...)` entry point and four internal step functions. Split into separate modules only when complexity makes a single file hard to maintain.

| Step function | Responsibility |
|---|---|
| `fetch(...)` | Retrieve source data and write raw development files. |
| `clean(...)` | Normalize provider data into bundle output shapes. |
| `save(...)` | Save cleaned development files under `data/storage/`; durable SQL waits for contracts. |
| `write_receipt(...)` | Emit success/failure completion receipt. |

## Outputs

Development outputs should be grouped by task/run:

```text
data/storage/<task-id-or-run-id>/
  task_key.json
  raw/
  cleaned/
  saved/
  receipt.json
```

## API Requirements

Document provider-specific requirements here:

- endpoint(s) or web source(s);
- required request parameters;
- pagination;
- rate limits;
- timestamp/timezone semantics;
- revision/vintage/as-of behavior;
- provider caveats;
- response fields used;
- response fields ignored.

## Tests And Fixtures

Default tests must use fixtures or mocks. Live calls require explicit opt-in guardrails.
