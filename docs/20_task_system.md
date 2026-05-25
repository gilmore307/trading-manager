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

Failures should become durable evidence, not chat-only notes. The failure register and agent-error helpers produce references that can be inspected, repaired, or escalated.

## Safety Gates

- Planning and materialization are safe by default.
- Provider calls require explicit provider dispatch.
- Runtime model lifecycle requests require accepted promotion or shadow-cycle evidence.
- Manager must not activate production pointers directly.
- Storage lifecycle mutation requires accepted lifecycle decision.
- Broker/account mutation is not allowed in manager.

## Model Research Run Cycle

Model research tasks are grouped by data reuse and decision-cycle ownership, not by a
linear Layer 1 through Layer 10 loop.

1. Foundation substrate. Build reusable market, sector, and global/sector event
   inputs once per historical window. This covers Layer 1, Layer 2, and the
   global or sector-scoped Layer 4 event substrate. It is reusable across target
   research runs; researching AAPL must not require redownloading the same
   reusable market, sector, macro, or global event evidence for NVDA.
2. Target substrate. Materialize target-specific source and feature evidence
   only when a downstream run needs it. This includes target state, target-local
   event slices, option-expression inputs, and other target-scoped source or
   feature rows. These tasks prepare what the live components would have been
   able to inspect, but they do not select a fixed trade target for replay.
3. Live-flow replay. Replay simulates the real system under a historical
   point-in-time background. Components may scan the eligible candidate pool,
   choose no target, choose one target, or choose a target combination. Replay
   must not be framed as "run this already selected symbol through the stack"
   unless the request is an explicit diagnostic repair scenario.
4. Failure attribution. After replay settlement and before evaluation judgment,
   a separate attribution task investigates misses, residuals, overblocks,
   underblocks, bad expressions, and event/co-event explanations. The same
   component boundary is needed in live operation after real decisions settle.
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

Trading Economics calendar handling is split into two manager-owned routes:

1. Historical seed: a one-time bootstrap from reviewed saved monthly `07_feed_trading_economics_calendar_web` CSV artifacts into `trading_data.source_10_event_risk_governor`. The planner merges all in-window rows across runs into one filtered per-month artifact, excludes wrong-window rows, and prepares a `source_10_event_risk_governor` task key. Raw monthly CSV originals may be deletion candidates only after successful SQL ingest and manifest review.
2. Recent poll: an ongoing realtime-maintenance task key for the logged-out visible recent calendar page. It uses `date_range_mode=recent`, `use_authenticated_cookies=false`, and no API/download/export route. The realtime system owns scheduling this poll and upserting planned/released macro events into SQL.
3. Due-release refresh: when a scheduled event reaches its release time, the realtime system should fetch immediately. If TE fetch fails or returns no released `actual`/`revised` value, retry every 10 seconds for 6 additional attempts, roughly 1 minute total retry time, under `te_recent_release_fetch_retry_10s_six_attempts_then_websearch`. If all attempts fail or the release still appears missing, fall back to `websearch_public_macro_release` to find either the released value or a documented delay/cancellation/no-release reason. Fallback rows must preserve provenance and must not be silently merged into TE-origin rows.

Training should read TE macro events from SQL first. If narrow gaps remain, the manager may fill them with reviewed logged-out visible-page custom-date fetches or public macro web-search provenance rows; fallback provenance must remain explicit. Ongoing TE maintenance does not depend on an active TE subscription.

## Useful Commands

```bash
PYTHONPATH=src python3 scripts/tasks/submit_manager_requests.py requests.jsonl
PYTHONPATH=src python3 scripts/tasks/materialize_request_payloads.py requests.jsonl --write-files
PYTHONPATH=src python3 scripts/tasks/validate_request_handoff.py --from-db --request-id mgrreq_example
PYTHONPATH=src python3 scripts/tasks/record_completion_receipt.py completion_receipt.json --request-id mgrreq_example --component-id component --repo-id trading-data --receipt-uri storage://example/receipt.json
PYTHONPATH=src python3 scripts/tasks/list_task_summary.py --limit 50
PYTHONPATH=src python3 scripts/tasks/rehearse_task_system.py --end-month 2016-01 --limit 3 --scenario mixed --format jsonl
PYTHONPATH=src python3 scripts/tasks/plan_trading_economics_calendar.py historical-seed --start-month 2016-01 --end-month 2026-05 --write-files
PYTHONPATH=src python3 scripts/tasks/plan_trading_economics_calendar.py recent-poll --lookahead-days 45 --write-files
```
