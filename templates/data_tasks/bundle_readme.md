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
- `idempotency_key`
- `data_domain`
- `acquisition_bundle`
- source/provider identifiers
- historical time range or snapshot timestamp
- provider-specific parameters
- development output destination under `TRADING_DATA_DEVELOPMENT_STORAGE_ROOT`
- completion receipt destination

Optional task key fields:

- symbols / underlyings / ETF ids / macro release key / calendar scope
- validation expectations
- retry expectations

## Step Modules

| Step | File | Responsibility |
|---|---|---|
| Fetch | `fetch.py` | Retrieve source data and write raw development files. |
| Clean | `clean.py` | Normalize provider data into bundle output shapes. |
| Save | `save.py` | Save cleaned development files under `data/storage/`; durable SQL waits for contracts. |
| Receipt | `receipt.py` | Emit success/failure completion receipt. |

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
