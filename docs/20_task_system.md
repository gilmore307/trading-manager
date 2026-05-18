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
- Model activation requires accepted agent promotion decision.
- Storage lifecycle mutation requires accepted lifecycle decision.
- Broker/account mutation is not allowed in manager.

## Trading Economics calendar maintenance

Trading Economics calendar handling is split into two manager-owned routes:

1. Historical seed: a one-time bootstrap from reviewed saved monthly `07_feed_trading_economics_calendar_web` CSV artifacts into `trading_data.source_09_event_risk_governor`. The planner merges all in-window rows across runs into one filtered per-month artifact, excludes wrong-window rows, and prepares a `source_09_event_risk_governor` task key. Raw monthly CSV originals may be deletion candidates only after successful SQL ingest and manifest review.
2. Recent poll: an ongoing realtime-maintenance task key for the logged-out visible recent calendar page. It uses `date_range_mode=recent`, `use_authenticated_cookies=false`, and no API/download/export route. The realtime system owns scheduling this poll and upserting planned/released macro events into SQL.
3. Due-release refresh: when a scheduled event reaches its release time, the realtime system should fetch immediately. If TE fetch fails or returns no released `actual`/`revised` value, retry every 10 seconds for 3 additional attempts under `te_recent_release_fetch_retry_10s_three_attempts_then_websearch`. If all attempts fail or the release still appears missing, fall back to `websearch_public_macro_release` to find either the released value or a documented delay/cancellation/no-release reason. Fallback rows must preserve provenance and must not be silently merged into TE-origin rows.

Training should read TE macro events from SQL first. If gaps remain, the manager may fill them with reviewed authenticated TE historical fetches or public macro web-search provenance rows; fallback provenance must remain explicit.

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
