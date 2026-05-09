# Task System

`trading-manager` owns the unified task control plane for all trading components.

The task system has two central responsibilities:

1. issue reviewed requests to component repositories;
2. record component completion receipts back into the shared control-plane tables.

It does not run provider calls, model training, broker mutations, dashboard rendering, or storage engines itself.

## Unified Lifecycle

```text
manager_request_v1
  -> component executes inside its own repository boundary
  -> component completion receipt JSON
  -> run_manifest_v1
  -> artifact_ref_v1 for the receipt/payload refs
  -> ready_signal_v1 when outputs are consumable
```

The manager uses the same lifecycle for data, model, storage, execution, and dashboard work. Component-local task queues may exist, but their private queue schemas do not become shared contracts.

## Request Ownership

Every cross-component request starts as `manager_request_v1` in `trading_manager.manager_request`.

The request row stores concise control-plane facts only:

- request id and kind;
- requester;
- target component/repository;
- expected output refs;
- policy refs;
- optional parameter ref;
- dry-run/live intent.

The parameter body belongs in storage behind `parameter_ref`; it is not embedded in manager SQL.

## Completion Receipt Ownership

A component completion receipt is the component's evidence that a requested run finished, failed, or produced partial output.

The component receipt payload may remain component/storage-owned JSON. Manager records the durable control-plane summary as:

- `run_manifest_v1` row per run;
- `artifact_ref_v1` row referencing the receipt payload;
- optional `artifact_ref_v1` rows for generic output refs listed by the receipt;
- `ready_signal_v1` row when the output is ready, partial, blocked, or failed.

Manager stores concise output references only. It does not copy large output lists, raw provider payloads, model vectors, logs, or broker payloads into SQL.

## Scripts

Validate or persist manager requests:

```bash
PYTHONPATH=src python3 scripts/tasks/submit_manager_requests.py requests.jsonl
PYTHONPATH=src python3 scripts/tasks/submit_manager_requests.py requests.jsonl --write
```

Normalize or persist a component receipt:

```bash
PYTHONPATH=src python3 scripts/tasks/record_completion_receipt.py completion_receipt.json \
  --request-id mgrreq_example \
  --component-id 01_feed_alpaca_bars \
  --component-kind data_feed \
  --repo-id trading-data \
  --receipt-uri storage://trading-data/example/completion_receipt.json
```

By default these scripts print normalized rows and do not mutate SQL. `--write` persists to the manager control-plane tables.

## Component Rules

- `trading-data` emits feed/source/feature receipts; manager records run/artifact/ready facts.
- `trading-model` emits generation/evaluation/review receipts; manager records run/artifact/ready facts.
- `trading-storage` owns durable payload storage, retention, backup, and rehydrate mechanics.
- `trading-execution` may receive manager requests, but broker order/fill/account payloads remain execution-owned.
- `trading-dashboard` receives ready/reviewed outputs for display, but dashboard widget schemas remain dashboard-owned.

## Guardrails

- A request is not proof that work happened.
- A receipt is not downstream approval unless it produces a compatible `ready_signal_v1`.
- `partial` receipts require review before downstream consumers rely on them.
- Failed receipts must remain queryable for audit, but they must not emit `ready` status.
- Secrets must be aliases/config refs only.
