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

For historical model training, manager is the scheduler/orchestrator. It should prepare and issue the layer-scoped component request set itself, not wait for an operator to manually prompt each feed, feature, or model step. Formal historical work must move chronological-forward from the accepted common start (`2016-01`) month by month; the scheduler should not jump to newer months before older eligible months are planned, dispatched, and received unless a reviewed operator exception is recorded. Operator review is reserved for boundary approvals such as live provider acquisition, promotion approval, or execution enablement. The long-running scheduler policy is defined in [`98_automation_scheduler.md`](98_automation_scheduler.md): keep safe historical work moving, but reserve capacity and regular-trading-day market-hours priority for live monitoring/execution.

`trading_manager.task_summary` is the global read model for all requests. It joins request, latest run, latest ready signal, and artifact counts so dashboards and operators can see every task in one priority-ordered surface.

## Request Ownership

Every cross-component request starts as `manager_request_v1` in `trading_manager.manager_request`.

The request row stores concise control-plane facts only:

- request id and kind;
- requester;
- target component/repository;
- expected output refs;
- policy refs;
- priority and optional deadline;
- optional parameter ref;
- dry-run/live intent.

The parameter body belongs in storage behind `parameter_ref`; it is not embedded in manager SQL. When a parameter payload is materialized, manager records the request-scoped payload reference as an `input_binding_v1` row rather than changing task state or pretending component execution has happened.

Accepted priority values, in descending order, are:

```text
critical
high
normal
low
backlog
```

`normal` is the default. The global summary sort order is `priority_rank`, then `deadline_at_utc`, then `created_at_utc`, then `request_id`.

## Completion Receipt Ownership

A component completion receipt is the component's evidence that a requested run finished, failed, or produced partial output.

The component receipt payload may remain component/storage-owned JSON. Manager records the durable control-plane summary as:

- `run_manifest_v1` row per run;
- `artifact_ref_v1` row referencing the receipt payload;
- optional `artifact_ref_v1` rows for generic output refs listed by the receipt;
- `ready_signal_v1` row when the output is ready, partial, blocked, or failed.

Manager stores concise output references only. It does not copy large output lists, raw provider payloads, model vectors, logs, or broker payloads into SQL. When component receipts report local `storage/...` output paths, manager normalizes them to repo-scoped `storage://<repo>/...` URIs and infers simple output metadata such as CSV media type and row count from receipt `row_counts` when explicit artifact objects are absent.

Artifact discovery is component-receipt-driven. Final `outputs` become downstream output artifacts; `steps.*.references` become supporting component artifacts such as `request_manifest`, `clean_equity_bar`, and `clean_schema`. Duplicate references are collapsed so the saved output is not counted twice when it appears in both `outputs` and a `save` step. These supporting artifacts may be attached to the ready signal for traceability, but they do not expand provider calls or imply stage-level coverage.

A task-level `ready_signal_v1` is not enough to unlock a workflow stage. Stage advancement must pass a `manager_stage_coverage_v1` gate over `task_summary`: for example, Layer 1 January 2016 data acquisition remains `partial_ready` at `3/22` ready requests and may unlock feature generation only at full expected coverage with `can_unlock_downstream=true`. Coverage accounting must preserve observed terminal states: an actual failed request remains in `failed_count`, even when later review accepts it as a normal historical absence. A stage may pass with `ready_count + accepted_failed_count >= expected_count` only when every failed request is covered by explicit agent failure-review evidence plus any required operator approval; it must not rewrite failures into ready rows. Accepted failed requests without an agent review reference are invalid.

Failed requests also belong in `trading_manager.failure_register`. The register records current state (`observed`, `agent_review_required`, `retry_required`, `corrected`, `accepted_skip`, or `unresolved`), the agent review artifact, correction evidence when applicable, and whether future matching requests should be skipped. A fixable failure should move to `corrected` only after the agent-reviewed fix evidence exists. A normal historical absence such as a not-yet-listed symbol may move to `accepted_skip`; future provider dispatch can then skip that exact registered request instead of repeating a known-useless call.

`trading-storage` provides `scripts/artifacts/store_completion_receipt_payload.py` for storage-owned receipt payload materialization. The emitted `artifact_ref_v1` metadata is what manager consumes through `record_completion_receipt.py`.

## Scripts

Validate or persist manager requests:

```bash
PYTHONPATH=src python3 scripts/tasks/submit_manager_requests.py requests.jsonl
PYTHONPATH=src python3 scripts/tasks/submit_manager_requests.py requests.jsonl --write
```

List the global task summary in priority order:

```bash
PYTHONPATH=src python3 scripts/tasks/list_task_summary.py --limit 50
```

Materialize request parameter payloads behind `parameter_ref` and optionally persist `input_binding_v1` metadata:

```bash
PYTHONPATH=src python3 scripts/tasks/materialize_request_payloads.py requests.jsonl --write-files

PYTHONPATH=src python3 scripts/tasks/materialize_request_payloads.py \
  --from-db \
  --request-kind data_backfill_month_v1 \
  --status requested \
  --write-files \
  --write-bindings
```

The second command is still handoff preparation only: it writes local task-key payloads and request-scoped input bindings, but it does not call providers or dispatch component work.

Run one scheduler tick to decide whether safe historical-training work can proceed under market-hours and resource gates:

```bash
PYTHONPATH=src python3 scripts/tasks/run_automation_scheduler.py \
  --start-month 2016-01 \
  --end-month 2016-01
```

By default this is plan-only and reports the next safe internal work item or explicit backoff reason. Add `--execute-safe-preparation` to let the scheduler write Layer 1 task-key payload files and validate handoff shape. This still performs no provider calls, model activation, or broker/execution work. Layer 1 Alpaca bar acquisition is the next internal historical-training stage; `live_call_approval_v1` is the safety gate for that stage, not an external manual dependency.

Prepare the first Layer 1 historical-training batch directly as one manager-owned operation:

```bash
PYTHONPATH=src python3 scripts/tasks/prepare_layer_one_historical_training.py \
  --start-month 2016-01 \
  --end-month 2016-01 \
  --write-files-only \
  --format json
```

This expands the reviewed Layer 1 market-regime ETF universe, materializes all `01_feed_alpaca_bars` task-key payloads, and validates component handoff shape in one batch. `--write` additionally persists manager request rows and input bindings to SQL. Neither mode calls providers, activates models, or touches broker/execution state.

Validate that a materialized payload is component-readable before dispatching work:

```bash
PYTHONPATH=src python3 scripts/tasks/validate_request_handoff.py \
  --from-db \
  --request-id mgrreq_backfill_alpaca_bars_2016_01
```

This imports the target `trading-data` feed pipeline and calls only `build_context`. It verifies the request, payload, hash-backed `input_binding_v1`, dry-run live-call policy, and component task-key shape. It does not call component `run`, does not call providers, does not write completion receipts, and does not change task status.

Validate a reviewed live-call approval artifact before converting a request into live provider handoff:

```bash
PYTHONPATH=src python3 scripts/tasks/validate_live_call_approval.py \
  live_requests.jsonl \
  --approval live_call_approval.json
```

`validate_live_call_approval.py` validates only the manager-side gate. It requires a non-dry-run `manager_request_v1` with `live_call_policy_required` and `live_call_approval_gate_v1` policy refs plus a `live_call_approval_v1` artifact with explicit approved request ids, provider allowlist, max request count, max window days, expiry, `approval_scope=provider_data_acquisition_only`, and `broker_execution_allowed=false`. It does not dispatch components, call providers, approve model promotion, or enable broker execution.

Provider dispatch is batch-aware. Use `--continue-on-error` only after the approval gate passes when individual provider/feed misses should become failed component receipts instead of aborting the entire approved batch. This keeps per-request failure evidence queryable in manager SQL while preserving the same approval scope and broker/model prohibitions.

Run a deterministic in-memory rehearsal of the request/receipt/summary lifecycle without provider calls or SQL writes:

```bash
PYTHONPATH=src python3 scripts/tasks/rehearse_task_system.py \
  --end-month 2016-01 \
  --limit 3 \
  --scenario mixed \
  --format jsonl
```

The mixed rehearsal emits one ready task, one partial task requiring review, and one failed task with a blocking reason. Rehearsal request ids are prefixed with `mgrreq_rehearsal_` and output refs stay under `storage://trading-manager/rehearsals/...` so they do not collide with future live request ids.

After reviewing the dry-run output, add `--write` to persist the same rehearsal-only rows to manager SQL tables and inspect them through `task_summary`:

```bash
PYTHONPATH=src python3 scripts/tasks/rehearse_task_system.py \
  --end-month 2016-01 \
  --limit 3 \
  --scenario mixed \
  --format jsonl \
  --write

PYTHONPATH=src python3 scripts/tasks/list_task_summary.py --limit 50
```

This is still not live component dispatch. It only exercises SQL persistence for rehearsal request/run/artifact/ready rows.

Plan a unified model promotion review request:

```bash
PYTHONPATH=src python3 scripts/tasks/plan_model_promotion_review.py \
  --model model_08_option_expression \
  --candidate-ref trading-model://promotion-candidates/mpcand_example
```

Store a receipt payload in `trading-storage`, then normalize or persist the manager rows:

```bash
# run from trading-storage
PYTHONPATH=src python3 scripts/artifacts/store_completion_receipt_payload.py completion_receipt.json \
  --request-id mgrreq_example \
  --run-id run_example \
  --producer-repo trading-data \
  --workflow-id 01_feed_alpaca_bars

# run from trading-manager
PYTHONPATH=src python3 scripts/tasks/record_completion_receipt.py completion_receipt.json \
  --request-id mgrreq_example \
  --component-id 01_feed_alpaca_bars \
  --component-kind data_feed \
  --repo-id trading-data \
  --receipt-uri storage://trading-data/example/completion_receipt.json
```

By default these scripts print normalized rows and do not mutate SQL. `--write` persists to the manager control-plane tables.

Check stage-level coverage before advancing downstream workflow stages:

```bash
PYTHONPATH=src python3 scripts/tasks/check_stage_coverage.py \
  --stage-id layer_01_market_regime.data_acquisition \
  --start-month 2016-01 \
  --end-month 2016-01 \
  --expected-count 22 \
  --write

PYTHONPATH=src python3 scripts/tasks/advance_model_training_workflow.py \
  --stage-coverage-report storage/runtime/stage_coverage/layer_01_market_regime_data_acquisition_2016-01.json \
  --write
```

The coverage report is evidence only when partial. It marks a workflow stage succeeded only when the report status is `ready` and `can_unlock_downstream=true`.

## Component Rules

- `trading-data` emits feed/source/feature receipts; manager records run/artifact/ready facts.
- `trading-model` emits generation/evaluation/review evidence receipts; manager records run/artifact/ready facts and owns the unified `model_promotion_review_v1` request entrypoint.
- `trading-storage` owns durable payload storage, retention, backup, and rehydrate mechanics.
- `trading-execution` may receive manager requests, but broker order/fill/account payloads remain execution-owned.
- `trading-dashboard` receives ready/reviewed outputs for display, but dashboard widget schemas remain dashboard-owned.

## Guardrails

- A request is not proof that work happened.
- A receipt is not downstream approval unless it produces a compatible `ready_signal_v1`.
- `partial` receipts require review before downstream consumers rely on them.
- `task_summary` is derived state; update the underlying request/run/ready rows rather than editing summary output.
- Failed receipts must remain queryable for audit, but they must not emit `ready` status.
- Manager-owned historical-training orchestration prepares whole layer batches; it must not degrade into manual one-request-at-a-time prompting.
- Formal historical work advances chronological-forward from `2016-01`; newer months must not leapfrog older eligible months without a reviewed operator exception.
- Historical work is background work relative to live monitoring/execution; the scheduler must respect resource budgets and market-hours protection only on regular US equity trading days during the protected window.
- Live provider acquisition requires a validated `live_call_approval_v1`; dry-run planning, payload materialization, and handoff validation are not approval.
- Live-call approval is data-acquisition-only; it must not permit broker orders, fills, account mutation, model activation, or execution-side lifecycle changes.
- Secrets must be aliases/config refs only.
