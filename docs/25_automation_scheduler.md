# Automation Scheduler

The scheduler selects safe historical-modeling work and advances it through explicit gates.

## Purpose

- Choose the next chronological and capacity-safe unit of work.
- Respect market-day/time and resource gates.
- Run safe offline preparation when allowed.
- Dispatch bounded provider stages only through explicit provider controls.
- Record decisions and checkpoints for resume.

## Work Classes

| Class | Example | Default posture |
|---|---|---|
| Safe planning | Build request previews, coverage reports, handoff payloads | Allowed. |
| Safe offline stage | Feature/materialization/model-local command with no broker mutation; provider access is allowed only when the stage explicitly declares it | Allowed only through reviewed executor path. |
| Provider dispatch | Alpaca/ThetaData/news/calendar backfill | Requires explicit dispatch gate. |
| Model activation | Promote production config | Requires accepted agent promotion decision. |
| Storage lifecycle mutation | Archive/delete/rehydrate | Requires accepted lifecycle decision. |
| Broker/account mutation | Orders, fills, positions, account state | Not allowed in manager. |

## Normal Commands

```bash
PYTHONPATH=src python3 scripts/tasks/run_automation_scheduler.py --start-month 2016-01 --end-month 2016-01
PYTHONPATH=src python3 scripts/tasks/run_automation_scheduler.py --start-month 2016-01 --end-month 2016-01 --execute-safe-preparation
PYTHONPATH=src python3 scripts/tasks/run_automation_scheduler_daemon.py --start-month 2016-01 --end-month 2016-01 --execute-safe-preparation --execute-safe-offline-stages --execute-autonomous-provider-stages --auto-select-next-work --advance-month-on-complete --once
```

## Foundation Priority

The scheduler should advance Layer 1/2 foundation coverage before ordinary Layer 3+ target work. Downstream target work requires an explicit selected target symbol once admitted.

Layer 2 feature generation also prepares `source_02_target_candidate_holdings` after sector context exists so downstream Layer 3 target-state feature generation can bind point-in-time sector/ETF context without manual SQL repair. Issuer holdings rows are accepted only inside their visible time window; historical windows with no official point-in-time holdings evidence remain empty instead of borrowing current holdings.

## Target Rotation

Layer 3+ model-worker training uses target-scoped fold checkpoints. The checked-in systemd template intentionally omits `--target-symbol`, so the daemon reads `runtime/model_training_target_queue.json` and selects the first queued target with an open or unstarted six-month model-worker fold. Supplying `--target-symbol` is a reviewed repair override that pins the daemon to one target and disables queue rotation for that run.

Accepted queue shape:

```json
{
  "contract_type": "manager_model_training_target_queue",
  "targets": [
    {"symbol": "AAPL"},
    {"symbol": "MSFT"}
  ]
}
```

If the first target has completed all eligible folds through the completed-month cutoff, the scheduler skips it and starts the next queued target from the earliest ready fold, usually `2016-01`. The queue controls execution routing only; it does not become fixed-target promotion evidence and does not replace Layer 3 candidate-policy replay.

The runtime queue can be prepared from reviewed target context mappings:

```bash
PYTHONPATH=src python3 scripts/tasks/prepare_model_worker_target_queue.py --write
```

## Event-Risk Lane

Layer 10 is part of the historical-modeling service boundary, but it is not a prerequisite for base-stack progression. It produces residual event-risk evidence, interventions, and promotion-review packets under the same no-broker safety rules.

## Dashboard Refresh Events

The resident service triggers the storage-owned dashboard read-model refresh whenever it writes workflow-state progress, including stage-start transitions. The storage refresh timer remains a fallback calibration route; it is not the primary dashboard progress path.
