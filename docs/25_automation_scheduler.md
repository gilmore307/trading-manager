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

Historical status surfaces expose one current task fact, not a future task
scaffold. Month checkpoints, fold states, and downstream blocked stages remain
internal scheduler evidence. The dashboard may show completed history and the
single current fold- or month-scoped task, with child partitions inside detail,
but it must not project later Layer 4-10 dependencies as independent Future
Tasks rows. A six-month fold opens only after its final calendar month has
completed in `America/New_York`, so `2026-fold1` is not eligible before
2026-07-01 even if some January-June child months already have source data.
Runtime execution advances one canonical month at a time. Historical scheduler
inputs may retain compatibility fields such as `month_ingest_workers`, but they
must not open multiple month lanes or project parallel month work into Tasks.

The service completes one fold's full run cycle before opening the next fold.
M01-M06 generation is the pre-replay boundary; it unlocks replay, replay
review, M06-linked residual-event governance checks, model evaluation,
promotion review, and maintenance/readiness handoff. Until that lifecycle emits maintenance/readiness
evidence, the next fold and next target stay internal workflow dependencies.

M01 background-context acquisition is the only reusable provider stage in the
foundation path. M03 event-state observation inputs are fold-scoped local
materializations, because accepted event families and M06-governed event
attributes can differ across folds.

M02 target-state materialization remains a local source-stage command. It turns
reviewed target-local `01_feed_alpaca_bars` artifacts into
`m03_target_state_vector_data_acquisition` migration-source rows and does not
call providers directly. When a target fold is blocked only by
`model_02_target_local_feed_artifacts_ready`, the scheduler may prepare and
dispatch bounded target-local Alpaca bar requests for the selected target
through the autonomous provider controls. Once those feed artifacts exist, the
normal safe offline M02 materialization stage continues.

M05 option-expression owns option-chain source acquisition. The shared
`trading_data.option_chain_state_source` table owns contract-level ThetaData
option-chain rows. Scheduler adds
`model_05_option_expression.option_chain_data_acquisition` only when the
selected target's metadata leaves listed options applicable. Targets marked as
`crypto_spot` or confirmed no-listed-options skip the option source/feature
stages, but M05 model generation still runs so no-option/not-applicable states
are represented in training.

Replay-selected listed option contracts require a second source boundary after
M05 has chosen a concrete contract. `model_group.replay_contract_paths` reads
the replay decision rows, prepares the bounded
`m05_option_expression_data_acquisition_contract_path` task key, and only calls
ThetaData selected-contract tracking when the explicit provider-acquisition gate
is enabled. Clean replay must retry after those path rows exist before treating
listed-option decisions as executable fills.

Source-existing bootstrap may seed M02 data acquisition from durable
`m03_target_state_vector_data_acquisition` rows for the selected target. That
prevents a clean control-plane reset from redownloading target-local bars when
the accepted source surface already covers the month.

## Model Group Reruns

The scheduler does not treat a rerun as "start the same tasks again." A rerun begins with a `model_group_rerun_plan` that names the earliest affected `layer.stage` cutpoint, the affected fold/target scope, concrete lifecycle candidates, protected and retained sets, controlled artifact roots, source-data lifecycle requirements, an embedded `storage_lifecycle_request`, and the scheduler reentry stage.

For ordinary architecture changes after acquisition, source data stays protected and the scheduler reenters at `feature_generation`, `model_generation`, or a later lifecycle stage. If the required source data itself changed, the rerun cutpoint is `data_acquisition`; the matching source partitions may become storage lifecycle candidates only within the plan's bounded provider/source/target/month/timeframe scope and only after artifact-index, storage lifecycle, protected-set, quarantine/recheck, and receipt gates allow any mutation.

Before reentry, workflow state after the cutpoint must be invalidated so completed rows do not cause false progress. A single-state reset writes `storage/02_control_plane/runtime/model_group_rerun_resets/<rerun_id>/...reset_receipt.json` as audit drill-down evidence for the cutpoint, preserved source roots, retained inherited artifacts, and allowed intermediate roots. A multi-state reset should also write one human-facing batch receipt under `storage/02_control_plane/runtime/model_group_rerun_resets/batches/`; operators should inspect the batch receipt first and open per-state receipts only when repairing a specific month or fold. During reentry, one resident scheduler owns the scope through its normal locks; launching a second same-scope daemon is invalid.

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

## Residual Event Governance

M06 is the residual-event governance model. It learns intervention,
overblock/underblock, missed-event, and underlying-vs-option failure attribution
after M04/M05 thesis formation and replay settlement. It does not appear as a
pre-replay provider data-acquisition lane.

M06 owns event-family attributes that describe where an event primarily acts,
including cases where option prices are affected more strongly than the
underlying price. M03 applies those attributes point-in-time as event state and
passes them through to M04/M05. M04 consumes the state for trade/no-trade
utility; M05 consumes it for option-expression suitability.

M06 attribution must separate model failure time from impact exposure time.
Event attribution uses `impact_exposure_time`, the earliest known time the
adverse or missed impact began to appear, as the causal cutoff; `decision_time`
is only a marked fallback. Impact severity is target-normalized when possible
using expected move, volatility, ATR, or an equivalent target context.

Event-family packets do not have to prove a linear directional relationship.
Scheduled releases, filings, earnings, macro events, and market-structure events
can have pre-release risk-state and post-release impact phases. Accepted packets
hand M03 a phase-aware state overlay, which downstream M04/M05 consume through
normal model state rather than ad hoc scheduler rules.

## Dashboard Refresh Events

The resident service triggers the storage-owned dashboard read-model refresh whenever it writes workflow-state progress, including stage-start transitions. The storage refresh timer remains a fallback calibration route; it is not the primary dashboard progress path.

## Progress Stall Guard

Historical automation must not sit in an apparently running but non-advancing state. The resident daemon treats ten minutes without executed scheduler progress as `scheduler_progress_stalled` and opens a server-wide agent error handoff for diagnosis/repair. Stage execution has the same ten-minute active-progress guard: if a running child process stops updating its task-progress file, the executor terminates the stage, records `stage_progress_stalled`, and routes it through the agent repair path. Waiting for a future incomplete calendar fold is the only normal no-progress exception.
