# Task System

`trading-manager` owns the unified task control plane for all trading components.

The task system has two central responsibilities:

1. issue reviewed requests to component repositories;
2. record component completion receipts back into the shared control-plane tables.

It does not run provider calls, model training, broker mutations, dashboard rendering, or storage engines itself.

## Unified Lifecycle

```text
manager_request
  -> component executes inside its own repository boundary
  -> component completion receipt JSON
  -> run_manifest
  -> artifact_ref for the receipt/payload refs
  -> ready_signal when outputs are consumable
```

The manager uses the same lifecycle for data, model, storage, execution, and dashboard work. Component-local task queues may exist, but their private queue schemas do not become shared contracts.

For historical model training, manager is the scheduler/orchestrator. It should prepare and issue the layer-scoped component request set itself, not wait for an operator to manually prompt each feed, feature, or model step. Formal historical work must move chronological-forward from the accepted common start (`2016-01`) month by month; the scheduler should not jump to newer months before older eligible months are planned, dispatched, and received unless a reviewed operator exception is recorded. Historical provider acquisition advances autonomously under manager controls; agent model-promotion decisions and rule-evaluated storage lifecycle decisions remain formal boundaries without becoming routine owner approval prompts. The owner observes and intervenes on issues instead of approving routine historical batches. Broker/order/fill/account mutation remains execution-library scope and is outside this historical modeling workflow. Realtime monitoring runtime control also remains execution-owned: manager may consume append-only realtime receipts/evidence, but must not start, stop, schedule, throttle, or reconnect realtime provider monitoring processes. The long-running scheduler policy is defined in [`98_automation_scheduler.md`](98_automation_scheduler.md): keep safe historical work moving, but reserve capacity and regular-trading-day market-hours priority for live monitoring/execution.

`trading_manager.task_summary` is the global read model for all requests. It joins request, latest run, latest ready signal, and artifact counts so dashboards and operators can see every task in one priority-ordered surface.

## Request Ownership

Every cross-component request starts as `manager_request` in `trading_manager.manager_request`.

The request row stores concise control-plane facts only:

- request id and kind;
- requester;
- target component/repository;
- expected output refs;
- policy refs;
- priority and optional deadline;
- optional parameter ref;
- dry-run/live intent.

The parameter body belongs in storage behind `parameter_ref`; it is not embedded in manager SQL. When a parameter payload is materialized, manager records the request-scoped payload reference as an `input_binding` row rather than changing task state or pretending component execution has happened.

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

- `run_manifest` row per run;
- `artifact_ref` row referencing the receipt payload;
- optional `artifact_ref` rows for generic output refs listed by the receipt;
- `ready_signal` row when the output is ready, partial, blocked, or failed.

Manager stores concise output references only. It does not copy large output lists, raw provider payloads, model vectors, logs, or broker payloads into SQL. When component receipts report local `storage/...` output paths, manager normalizes them to repo-scoped `storage://<repo>/...` URIs and infers simple output metadata such as CSV media type and row count from receipt `row_counts` when explicit artifact objects are absent.

Artifact discovery is component-receipt-driven. Final `outputs` become downstream output artifacts; `steps.*.references` become supporting component artifacts such as `request_manifest`, `clean_equity_bar`, and `clean_schema`. Duplicate references are collapsed so the saved output is not counted twice when it appears in both `outputs` and a `save` step. These supporting artifacts may be attached to the ready signal for traceability, but they do not expand provider calls or imply stage-level coverage.

A task-level `ready_signal` is not enough to unlock a workflow stage. Stage advancement must pass a `manager_stage_coverage` gate over `task_summary`: for example, Layer 1 January 2016 data acquisition remains `partial_ready` at `3/22` ready requests and may unlock feature generation only at full expected coverage with `can_unlock_downstream=true`. Coverage accounting must preserve observed terminal states: an actual failed request remains in `failed_count`, even when later review accepts it as a normal historical absence. A stage may pass with `ready_count + accepted_failed_count >= expected_count` only when every failed request is covered by explicit agent failure-review evidence plus any required review artifact; it must not rewrite failures into ready rows. Accepted failed requests without an agent review reference are invalid.

Failed requests also belong in `trading_manager.failure_register`. The register records current state (`observed`, `agent_review_required`, `retry_required`, `corrected`, `accepted_skip`, or `unresolved`), the agent review artifact, correction evidence when applicable, and whether future matching requests should be skipped. A fixable failure should move to `corrected` only after the agent-reviewed fix evidence exists. A normal historical absence such as a not-yet-listed symbol may move to `accepted_skip`; future provider dispatch can then skip that exact registered request instead of repeating a known-useless call. When the not-yet-listed fact is clear before dispatch, a preflight agent review may register `accepted_skip` without making the known-useless provider call; stage coverage counts that row as a reviewed terminal skip, not as a ready output.

`trading-storage` provides `scripts/artifacts/store_completion_receipt_payload.py` for storage-owned receipt payload materialization. The emitted `artifact_ref` metadata is what manager consumes through `record_completion_receipt.py`.

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

Materialize request parameter payloads behind `parameter_ref` and optionally persist `input_binding` metadata:

```bash
PYTHONPATH=src python3 scripts/tasks/materialize_request_payloads.py requests.jsonl --write-files

PYTHONPATH=src python3 scripts/tasks/materialize_request_payloads.py \
  --from-db \
  --request-kind data_backfill_month \
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

By default this is plan-only and reports the next internal work item or explicit backoff reason. Add `--execute-safe-preparation` to let the scheduler write task-key payload files and validate handoff shape. Preparation still performs no provider calls, model activation, or broker/execution work. After payloads exist, Layer 1/2 Alpaca bar acquisition advances through `--execute-autonomous-provider-stages`, which executes at most one bounded autonomous provider dispatch/reconcile slice per tick under resource/terminal-coverage guards.

Prepare the first Layer 1 historical-training batch directly as one manager-owned operation:

```bash
PYTHONPATH=src python3 scripts/tasks/prepare_layer_one_historical_training.py \
  --start-month 2016-01 \
  --end-month 2016-01 \
  --write-files-only \
  --format json
```

This expands the reviewed Layer 1 market-regime ETF universe, materializes all `01_feed_alpaca_bars` task-key payloads, and validates component handoff shape in one batch. `--write` additionally persists manager request rows and input bindings to SQL. Neither mode calls providers, activates models, or touches broker/execution state.

Prepare the Layer 2 sector-context historical-training batch through the same no-provider boundary:

```bash
PYTHONPATH=src python3 scripts/tasks/prepare_layer_two_historical_training.py \
  --start-month 2016-01 \
  --end-month 2016-01 \
  --write-files-only \
  --format json
```

Layer 2 stage coverage is separate from Layer 1 even though both use `01_feed_alpaca_bars`; coverage matches the reviewed model-layer universe/request ids so same-month Layer 1 and Layer 2 rows cannot contaminate each other.

Materialize Layer 3 target-state source inputs from already reviewed Layer 2 feed artifacts:

```bash
PYTHONPATH=src python3 scripts/tasks/materialize_layer_three_target_state_inputs.py \
  --start-month 2016-01 \
  --end-month 2016-01 \
  --write
```

This emits `manager_layer_three_target_state_input_materialization` evidence, merges completed Layer 2 Alpaca bar artifacts into a `source_03_target_state` task key, and delegates normalization to `trading-data`. It performs zero provider calls, zero model activation, zero broker execution, and no storage lifecycle mutation.

Materialize Layer 4 event-overlay inputs from local source-detector outputs over already reviewed Layer 2 feed artifacts:

```bash
PYTHONPATH=src python3 scripts/tasks/materialize_layer_four_event_overlay_inputs.py \
  --start-month 2016-01 \
  --end-month 2016-01 \
  --write
```

This emits `manager_layer_four_event_overlay_input_materialization` evidence, runs only the local `source_04_event_overlay.equity_abnormal_activity` detector over saved bar CSV artifacts, then writes compact detector/residual event overview rows through `source_04_event_overlay`. It performs zero provider calls, zero model activation, zero broker execution, and no storage lifecycle mutation. The detector may cite saved bars/liquidity as provenance, but manager must not treat ordinary bar/liquidity features already consumed by the base model stack as new independent event alpha. Layer 2 feed artifacts with zero saved bar rows are recorded as `skipped_zero_bar_rows` before detector execution; this preserves not-yet-listed/no-data evidence without failing the local detector. Required event-feed artifacts must exist and report nonzero requested-window row coverage before write mode can proceed. If all executed local detectors emit zero events, the stage must stop for an explicit no-event context policy review instead of fabricating event rows.

Record a realtime shadow decision handoff receipt when execution/model scaffolds have produced a realtime decision input snapshot and model route plan:

```bash
PYTHONPATH=src python3 scripts/tasks/record_realtime_shadow_handoff.py \
  --decision-input decision_input.json \
  --route-plan route_plan.json \
  --output bundle
```

The output is `manager_realtime_shadow_handoff_control_plane_bundle`: a standard component completion receipt plus normalized `run_manifest`, `artifact_ref`, and `ready_signal` rows. It makes the execution -> model realtime shadow handoff visible to manager/task-summary consumers without model activation, broker calls, order construction, or account mutation. This is evidence consumption, not realtime runtime control: manager must not use this path to start/stop streams, schedule subscriptions, throttle providers, or reconnect monitoring processes. Realtime evidence should be persisted as lightweight decision-effectiveness metrics once labels mature, not as historical test-set rows by default. Add `--persist-normalized-rows` only when a durable receipt URI/database context is reviewed and manager SQL persistence is explicitly desired.

Rehearse the full cross-repository fixture chain when validating realtime wiring:

```bash
PYTHONPATH=src python3 scripts/tasks/rehearse_realtime_shadow_handoff.py \
  --decision-time 2026-05-11T13:30:00+00:00 \
  --historical-dataset-snapshot-ref trading-model://snapshots/historical/unit \
  --frozen-model-config-ref trading-model://configs/frozen/unit
```

The rehearsal invokes execution fixture builders, model route-plan validation, and manager receipt normalization, but still performs zero provider calls, model activation, broker calls, order construction, persistence, or account mutation.

After Layer 3 is complete, base Layers 4-7 may advance through the safe offline executor by reading already-persisted SQL rows without requiring event-overlay/source_04 inputs:

- Base Layer 4 reads Layer 1-3 target context and writes the legacy physical `trading_model.model_05_alpha_confidence`.
- Base Layer 5 reads alpha confidence and writes the legacy physical `trading_model.model_06_position_projection` using flat/no-pending position context defaults.
- Base Layer 6 reads Layer 5 projection context and writes the legacy physical `trading_model.model_07_underlying_action` as offline planning evidence only.
- Base Layer 7 reads the completed Layer 6 chain and writes legacy option-expression/trading-guidance evidence through `trading_model.model_08_option_expression` when the reviewed gate admits it.

These stages remain safe only while the stage receipts show `provider_calls=0`, `model_activation_performed=false`, and `broker_execution_performed=false`; promotion review output remains evidence until the agent promotion-decision path approves or defers activation.

Before base Layer 7 trading-guidance / legacy option-expression acquisition, review the completed Layer 6 target chain without calling providers:

```bash
PYTHONPATH=src python3 scripts/tasks/review_layer_eight_option_expression_gate.py \
  --start-month 2016-01 \
  --end-month 2016-01 \
  --write
```

The legacy artifact is still `manager_layer_08_option_expression_gate_review` until the physical implementation is renamed. It reads `trading_model.model_07_underlying_action`, previews future `source_05_option_expression` / ThetaData option-snapshot requests only for active base Layer 6 action chains, and records a reviewed no-provider skip when all action rows are no-trade/maintain/neutral. This review performs zero provider calls, zero broker execution, zero model activation, and zero storage lifecycle mutation. If active request previews exist, the next action is bounded autonomous provider dispatch; if no active request previews exist, the review itself is sufficient evidence to complete base Layer 7 data acquisition as a no-provider skip.

Base Layer 7 legacy option-expression feature generation runs through the manager adapter `scripts/tasks/execute_layer_eight_option_feature_generation.py`. When the gate review is `no_provider_skip_accepted` with zero active requests, the adapter writes `layer_08_option_expression_feature_generation_no_provider_skip_receipt_YYYY-MM.json` and treats `feature_08_option_expression` as a reviewed no-op. When active option requests were approved and acquired, the same adapter delegates to trading-data `feature_08_option_expression` with month-scoped source windows.

Validate that a materialized payload is component-readable before dispatching work:

```bash
PYTHONPATH=src python3 scripts/tasks/validate_request_handoff.py \
  --from-db \
  --request-id mgrreq_backfill_alpaca_bars_2016_01
```

This imports the target `trading-data` feed pipeline and calls only `build_context`. It verifies the request, payload, hash-backed `input_binding`, dry-run manager controls, and component task-key shape. It does not call component `run`, does not call providers, does not write completion receipts, and does not change task status.

Dispatch historical provider acquisition autonomously when the stage dashboard shows pending request ids:

```bash
PYTHONPATH=src python3 scripts/tasks/dispatch_and_reconcile_provider_stage.py \
  --model-layer layer_02_sector_context \
  --start-month 2016-01 \
  --end-month 2016-01 \
  --execute-provider-calls \
  --continue-on-error \
  --skip-registered-failures \
  --reject-terminal-coverage
```

The active historical provider path no longer has a per-batch manual gate. It dispatches bounded manager request ids under resource controls, terminal-coverage rejection, receipts, and failure registration. It still does not activate models, construct or execute broker orders, mutate accounts, or perform storage lifecycle mutation.

For normal operation, use the stage-run dashboard as the single operator-facing entry point:

```bash
PYTHONPATH=src python3 scripts/tasks/summarize_stage_run.py \
  --stage-id layer_02_sector_context.data_acquisition \
  --start-month 2016-01 \
  --end-month 2016-01 \
  --next-limit 5 \
  --write
```

The dashboard artifact is `manager_stage_run_dashboard`. It summarizes stage coverage, observed provider calls, evidence refs, the next autonomous provider-dispatch preview, and the next safe action.

Workflow checkpoints keep `provider_calls` as the safe/offline stage counter and record acquisition calls from ingested receipts in `provider_calls_observed`. This preserves the safety invariant that offline stages report zero provider calls while still making month-level acquisition volume visible to dashboards and audits.

For the simplest control loop, run one controller step:

```bash
PYTHONPATH=src python3 scripts/tasks/run_stage_controller.py \
  --stage-id layer_02_sector_context.data_acquisition \
  --start-month 2016-01 \
  --end-month 2016-01 \
  --next-limit 5 \
  --write
```

The controller emits `manager_stage_run_controller_receipt`, refreshes the dashboard, and may execute the next bounded autonomous provider-dispatch slice. It still stops at broker/order/fill/account mutation, and model/storage mutations require their own agent decision artifacts.

Provider dispatch is batch-aware. Plan-only dispatch prints commands without provider calls; actual `--execute-provider-calls` runs autonomous historical acquisition for bounded request ids, strips retired approval-policy refs from runtime task keys, and preserves broker/model prohibitions. Use `--continue-on-error` only when individual provider/feed misses should become failed component receipts instead of aborting the batch.

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

After an provider batch has produced component receipts, reconcile the stage in one safe offline pass:

```bash
PYTHONPATH=src python3 scripts/tasks/reconcile_provider_stage.py \
  --stage-id layer_02_sector_context.data_acquisition \
  --start-month 2016-01 \
  --end-month 2016-01 \
  --write-control-plane \
  --write-coverage-report \
  --coverage-report-path storage/runtime/stage_coverage/layer_02_sector_context_data_acquisition_2016-01.json \
  --advance-workflow \
  --write-workflow-state
```

`reconcile_provider_stage.py` discovers existing completion receipts, normalizes `run_manifest` / `artifact_ref` / `ready_signal` rows, refreshes `manager_stage_coverage`, and can ingest that written coverage report into workflow state. With `--write-failure-proposal`, failed receipts also produce JSONL `manager_failure_register` proposal rows with `failure_status=agent_review_required`; with `--write-failure-register`, those observed failures may be persisted for review. This preserves failed facts but does not accept, skip, correct, or retry any failure until a later agent review changes the disposition. The reconcile script never dispatches components, calls providers, activates models, mutates broker state, or executes storage lifecycle actions.

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
- `trading-model` emits generation/evaluation/review evidence receipts; manager records run/artifact/ready facts and owns the unified `model_promotion_review` request entrypoint.
- `trading-storage` owns durable payload storage, retention, backup, and rehydrate mechanics.
- `trading-execution` may receive manager requests, but broker order/fill/account payloads remain execution-owned.
- `trading-dashboard` receives ready/reviewed outputs for display, but dashboard widget schemas remain dashboard-owned.

## Guardrails

- A request is not proof that work happened.
- A receipt is not downstream approval unless it produces a compatible `ready_signal`.
- `partial` receipts require review before downstream consumers rely on them.
- `task_summary` is derived state; update the underlying request/run/ready rows rather than editing summary output.
- Failed receipts must remain queryable for audit, but they must not emit `ready` status.
- Manager-owned historical-training orchestration prepares whole layer batches; it must not degrade into manual one-request-at-a-time prompting.
- Formal historical work advances chronological-forward from `2016-01`; newer months must not leapfrog older eligible months without a reviewed operator exception.
- Historical work is background work relative to live monitoring/execution; the scheduler must respect resource budgets and market-hours protection only on regular US equity trading days during the protected window.
- Historical provider acquisition is autonomous after manager payload preparation; dry-run planning, payload materialization, and handoff validation remain no-provider preparation. Broker/order/account mutation remains execution-owned, and model activation still requires a separate agent promotion decision.
- Autonomous provider dispatch is data-acquisition-only; it must not permit broker orders, fills, account mutation, model activation, or execution-side lifecycle changes.
- Secrets must be aliases/config refs only.
