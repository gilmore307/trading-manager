# Automation Scheduler

The scheduler selects safe historical-modeling work and advances it through explicit gates.

## Purpose

- Choose the next chronological and capacity-safe unit of work.
- Respect market-day/time and resource gates.
- Pause historical model tasks while future live runtime is enabled.
- Run safe offline preparation when allowed.
- Dispatch bounded provider stages only through explicit provider controls.
- Record decisions and checkpoints for resume.

## Live Runtime Pause

When future live runtime is enabled, historical model tasks are paused. This is
stronger than ordinary market-hours protection: the scheduler returns
`live_runtime_historical_model_tasks_paused` and selects no historical work so
realtime trading, market-data ingestion, broker gates, account freshness, and
C08 model-group comparison keep priority.

The gate is controlled by `TRADING_MANAGER_LIVE_RUNTIME_MODE_ENABLED=1` or the
one-shot scheduler flag:

```bash
PYTHONPATH=src python3 scripts/tasks/run_automation_scheduler.py --live-runtime-mode
```

## Work Classes

| Class | Example | Default posture |
|---|---|---|
| Safe planning | Build request previews, coverage reports, handoff payloads | Allowed. |
| Safe offline stage | Feature/materialization/model-local command with no broker mutation; provider access is allowed only when the stage explicitly declares it | Allowed only through reviewed executor path. |
| Provider dispatch | Alpaca/ThetaData/news/calendar backfill | Requires explicit dispatch gate. |
| Runtime model lifecycle request | Ask runtime lifecycle owner to classify active/shadow/candidate roles | Requires accepted promotion or shadow-cycle evidence; manager does not activate pointers. |
| Storage lifecycle mutation | Archive/delete/rehydrate | Requires accepted lifecycle decision. |
| Broker/account mutation | Orders, fills, positions, account state | Not allowed in manager. |

## Normal Commands

```bash
PYTHONPATH=src python3 scripts/tasks/run_automation_scheduler.py --start-month 2016-01 --end-month 2016-01
PYTHONPATH=src python3 scripts/tasks/run_automation_scheduler.py --start-month 2016-01 --end-month 2016-01 --execute-safe-preparation
PYTHONPATH=src python3 scripts/tasks/run_automation_scheduler_daemon.py --start-month 2016-01 --end-month 2016-01 --execute-safe-preparation --execute-safe-offline-stages --execute-autonomous-provider-stages --auto-select-next-work --advance-month-on-complete --once
```

## Research-Cycle Priority

The scheduler should advance reusable foundation coverage before ordinary target substrate work. Foundation coverage includes Layer 1 market context, Layer 2 sector context, and fold-scoped global or sector-scoped Layer 4 event-observation substrate. Layer 4 event-observation collection repeats per fold because the accepted observation pool may change between folds. These rows are shared across target research runs and must not be redownloaded merely because a new target is being studied.

Historical training status surfaces use fold identity globally. Month-level
provider batching and old month checkpoint files are implementation detail;
the dashboard and owner-facing task inventory should show fold tasks with
month child partitions rather than mixing Layer 1/2 month rows with Layer 3+
fold rows. A six-month fold opens only after its final calendar month has
completed in `America/New_York`, so `2026-fold1` is not eligible before
2026-07-01 even if some January-June child months already have source data.

The service completes one fold's full run cycle before opening the next fold.
Layer 1-9 completion is only the pre-replay boundary; it unlocks Replay, Layer
10 Event Risk Governor attribution, Model Evaluation, Model Promotion, and
Model Maintenance. Until that lifecycle emits maintenance/readiness evidence,
the next fold and the next target remain blocked because Layer 10 may update
the event-observation pool used by later Layer 4 folds.

Layer 2 feature generation also prepares `m02_sector_context_data_acquisition` after sector context exists so downstream Layer 3 target-state feature generation can bind point-in-time sector/ETF context without manual SQL repair. Issuer holdings rows are accepted only inside their visible time window; historical windows with no official point-in-time holdings evidence remain empty instead of borrowing current holdings.

## Model Group Reruns

The scheduler does not treat a rerun as "start the same tasks again." A rerun begins with a `model_group_rerun_plan` that names the earliest affected `layer.stage` cutpoint, the affected fold/target scope, a concrete delete set, a protected set, source-data deletion requirements, and the scheduler reentry stage.

For ordinary architecture changes after acquisition, source data stays protected and the scheduler reenters at `feature_generation`, `model_generation`, or a later lifecycle stage. If the required source data itself changed, the rerun cutpoint is `data_acquisition`; the matching source partitions may be deleted only within the plan's bounded provider/source/target/month/timeframe scope and only after storage lifecycle/protected-set gates allow the mutation.

Before reentry, workflow state after the cutpoint must be invalidated so completed rows do not cause false progress. During reentry, one resident scheduler owns the scope through its normal locks; launching a second same-scope daemon is invalid.

## Target Rotation

Target substrate work uses target-scoped checkpoints only for data preparation and diagnostics. It does not mean replay is forced to trade that target. Live-flow replay must simulate the real component graph over the eligible historical candidate pool, where components may select no target, one target, or a target combination.

The checked-in systemd template may omit `--target-symbol` so the daemon can advance a reviewed substrate queue. Supplying `--target-symbol` is a reviewed repair override for preparing or repairing one target's data lane; it must not be treated as promotion evidence for a fixed-target strategy.

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

If the first target has completed all eligible substrate windows through the completed-fold cutoff and its current fold lifecycle has completed maintenance/readiness handoff, the scheduler skips it and starts the next queued target from the earliest ready window, usually `2016-01`. The queue controls data-preparation routing only; it does not become fixed-target promotion evidence and does not replace component-led candidate selection replay.

The runtime queue can be prepared from reviewed target context mappings:

```bash
PYTHONPATH=src python3 scripts/tasks/prepare_model_worker_target_queue.py --write
```

## Event-Risk Lane

Layer 10 is part of the historical-modeling service boundary, but it starts after concentrated live-flow replay has produced settled replay traces, failures, residuals, misses, or deviations. It must not appear as a pre-replay data-acquisition or feature-generation stage. Post-replay attribution may inspect target selection misses, portfolio combinations, Layer 4 event-risk behavior, Layer 5 alpha errors, Layer 6/7/8 position-management choices, Layer 9 option-expression drag, and Layer 10 event/co-event explanations. It produces attribution packets for evaluation and, where appropriate, event-family promotion-review packets under the same no-broker safety rules.

## Dashboard Refresh Events

The resident service triggers the storage-owned dashboard read-model refresh whenever it writes workflow-state progress, including stage-start transitions. The storage refresh timer remains a fallback calibration route; it is not the primary dashboard progress path.
