# Task System

The task system is the manager control-plane lifecycle for component work.

## Lifecycle

```text
1. Manager creates or previews a request.
2. Manager materializes parameter/input payloads by reference.
3. Manager validates the handoff boundary.
4. A component performs work.
5. The component emits a completion receipt.
6. Manager normalizes run/artifact/ready rows.
7. Manager surfaces task summary, failure evidence, and next action.
```

## Core Rows

- `manager_request` — requested work.
- `input_binding` — approved input refs.
- `run_manifest` — component run summary.
- `run_step` — optional step detail.
- `artifact_ref` — output refs.
- `ready_signal` — declared readiness for a consumer scope.
- `task_summary` — derived read model; it does not own state.

## Priority Values

```text
critical | high | normal | low | backlog
```

Default priority is `normal`. Summary ordering is priority, deadline, created time, then request id.

## Failure Handling

Failures should become durable evidence, not chat-only notes. The failure register and agent-error helpers produce references that can be inspected, repaired, or escalated. The reviewed Codex error-repair runner uses `danger-full-access` so the `server-error-repair` closed-loop contract can commit/push maintained fixes and rerun internal database-backed stages; the prompt boundary still forbids broker/account/order/fill/position mutation and secret exposure.

## Safety Gates

- Planning and materialization are safe by default.
- Provider calls require explicit provider dispatch.
- Runtime model lifecycle requests require accepted promotion or shadow-cycle evidence.
- Manager must not activate production pointers directly.
- Storage lifecycle mutation requires accepted lifecycle decision.
- Broker/account mutation is not allowed in manager.
- Live-enabled provider runtime task keys are execution scratch. The canonical prepared source task key remains under its request path; successful provider dispatch removes the runtime copy after the subprocess consumes it, while failed dispatch retains the runtime copy for diagnosis.

## Model Research Run Cycle

Model research tasks are grouped by data reuse and decision-cycle ownership, not by a
linear Layer 1 through Layer 10 loop.

The public task unit for historical training is the six-month fold. Month
coverage remains visible as child partition evidence under the fold, but the
operator-facing task list should not switch between month-scoped Layer 1/2
work and fold-scoped downstream work.

1. Foundation substrate. Build reusable market, sector, and fold-scoped
   global/sector event inputs for each historical window. This covers Layer 1,
   Layer 2, and the global or sector-scoped Layer 4 event-observation substrate.
   The Layer 4 event substrate is still collected per fold because the accepted
   event observation pool can change across folds; researching AAPL must not
   require redownloading the same reusable market, sector, macro, or global
   event evidence for NVDA.
2. Target substrate. Materialize target-specific source and feature evidence
   only when a downstream run needs it. This includes target state, target-local
   event slices, option-expression inputs, and other target-scoped source or
   feature rows. If the selected target lacks reviewed target-local bar
   artifacts for a fold, manager prepares bounded `01_feed_alpaca_bars` requests
   for that target and dispatches them through the autonomous provider gate; the
   Layer 3 `m03_target_state_vector_data_acquisition` materializer then consumes those local
   artifacts without direct provider access. These tasks prepare what the live
   components would have been able to inspect, but they do not select a fixed
   trade target for replay.
3. Live-flow replay. Replay simulates the real system under a historical
   point-in-time background. Components may scan the eligible candidate pool,
   choose no target, choose one target, or choose a target combination. Replay
   must not be framed as "run this already selected symbol through the stack"
   unless the request is an explicit diagnostic repair scenario.
4. Failure attribution and Layer 10. After replay settlement and before
   evaluation judgment, a separate attribution task investigates misses,
   residuals, overblocks, underblocks, bad expressions, and event/co-event
   explanations. Layer 10 starts here; it must not run as a pre-replay
   data-acquisition or feature-generation stage. The same component boundary is
   needed in live operation after real decisions settle.
5. Evaluation. Evaluation consumes replay traces and attribution packets to
   score the candidate component bundle against baselines, calibration,
   stability, leakage, portfolio behavior, and failure explanations.
6. Promotion and lifecycle handoff. Promotion produces accepted/rejected/deferred
   evidence for a model bundle. Management of already promoted models belongs to
   the runtime component lifecycle owner, not to manager activation.

The manager schedules and records these tasks. It does not turn a historical
target-substrate request into a fixed-target strategy claim, and it does not
activate promoted models directly.

## Trading Economics calendar maintenance

Trading Economics calendar handling has one accepted source route:

1. Canonical source: reviewed TE calendar payloads under `trading-storage/storage/01_source_data/monthly_backfill/trading_economics_calendar_web/YYYY-MM/runs/<run_id>/`. These files are append-only protected and Git-recoverable.
2. Derived materializations: SQL rows, runtime receipts, control-plane filtered artifacts, and dashboard read models are rebuildable operational/materialized state, not the source of truth. TE macro rows should stay out of `m10_event_risk_governor_data_acquisition` and dashboard event markers until Layer 10 explicitly promotes macro events into the accepted event-risk/attention pool.

Manager workflows may schedule the bounded recent/future Trading Economics calendar refresh into canonical storage source rows. They must not record TE website URLs as source references, must not write TE macro rows into `m10_event_risk_governor_data_acquisition`, and must not silently merge public web-search fallback rows into TE-origin source data.

TE refresh creates normal daily Git changes in the canonical source-data tree. Maintenance commits should include those changed/new TE source files with the code or docs batch when they are relevant to the same acceptance window; their presence in `git status` is not a cleanup problem. Rerun resets must preserve these files, record the TE root in `protected_set`/`retained_set`, and never delete TE canonical source data.

## Useful Commands

```bash
PYTHONPATH=src python3 scripts/tasks/submit_manager_requests.py requests.jsonl
PYTHONPATH=src python3 scripts/tasks/materialize_request_payloads.py requests.jsonl --write-files
PYTHONPATH=src python3 scripts/tasks/validate_request_handoff.py --from-db --request-id mgrreq_example
PYTHONPATH=src python3 scripts/tasks/record_completion_receipt.py completion_receipt.json --request-id mgrreq_example --component-id component --repo-id trading-data --receipt-uri storage://example/receipt.json
PYTHONPATH=src python3 scripts/tasks/list_task_summary.py --limit 50
PYTHONPATH=src python3 scripts/tasks/rehearse_task_system.py --end-month 2016-01 --limit 3 --scenario mixed --format jsonl
# Retired/inventory only; does not create source_10 task keys.
PYTHONPATH=src python3 scripts/tasks/plan_trading_economics_calendar.py historical-seed --start-month 2016-01 --end-month 2026-05
```
