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
| Safe offline stage | Feature/materialization/model-local command with no provider/broker mutation | Allowed only through reviewed executor path. |
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

## Event-Risk Lane

Layer 9 is part of the historical-modeling service boundary, but it is not a prerequisite for base-stack progression. It produces residual event-risk evidence, interventions, and promotion-review packets under the same no-broker safety rules.

## Dashboard Refresh Events

The resident service triggers the storage-owned dashboard read-model refresh whenever it writes workflow-state progress, including stage-start transitions. The storage refresh timer remains a fallback calibration route; it is not the primary dashboard progress path.
