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
Layer 1-9 completion is only the pre-replay boundary; it unlocks Replay, Layer
10 Event Risk Governor attribution, Model Evaluation, Model Promotion, and
Model Maintenance. Until that lifecycle emits maintenance/readiness evidence,
the next fold and the next target stay internal workflow dependencies because
Layer 10 may update the event-observation pool used by later Layer 4 folds.

Layer 2 feature generation prepares sector/context features only. It does not fetch ETF holdings or materialize target-candidate holdings. Downstream Layer 3 target-state feature generation consumes target-local evidence and accepted target-context mappings; historical replay candidate coverage comes from the fixed historical candidate-universe table and matching replay bars rather than the mutable realtime total pool or current ETF holdings.

Layer 3 target-state materialization remains a local source-stage command: it
turns reviewed target-local `01_feed_alpaca_bars` artifacts into
`m03_target_state_vector_data_acquisition` and does not call providers. When a target fold is
blocked only by `layer_03_target_local_feed_artifacts_ready`, the scheduler may
prepare and dispatch bounded target-local Alpaca bar requests for the selected
target through the same autonomous provider controls used by Layer 1/2. Once
those feed artifacts exist, the normal safe offline L3 materialization stage
continues.

Layer 3 option context is not a separate contract route. The shared
`trading_data.option_chain_state_source` table owns contract-level ThetaData
option-chain rows. Layer 3 feature generation reads it only as an optional
target-level option-chain reducer input, while Layer 9 reuses the same source to
derive option-expression candidate rows. Scheduler adds this source stage only
when the selected target's metadata leaves listed options applicable. Targets
marked as `crypto_spot` or confirmed no-listed-options do not get a Layer 3
option-chain stage, Layer 3 option payload fields, or Layer 9 option-expression
stages.

Source-existing bootstrap may seed Layer 3 data acquisition from durable
`m03_target_state_vector_data_acquisition` rows for the selected target. That prevents a clean
control-plane reset from redownloading target-local bars when the accepted source
surface already covers the month.

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

## Event-Risk Lane

Layer 10 is part of the historical-modeling service boundary, but it starts after concentrated live-flow replay has produced settled replay traces, failures, residuals, misses, or deviations. It must not appear as a pre-replay data-acquisition or feature-generation stage. Post-replay work has two scheduler steps: replay failure triage identifies failed fills, missed winners, and other residual rows; Layer 10 EventRiskGovernor attribution then consumes that triage plus reviewed point-in-time event observations or candidates. If the event evidence is missing, the scheduler backs off and prepares bounded event-feed backfill task keys for the failure scope without provider calls. Once event observations are materialized, Layer 10 may inspect target selection misses, portfolio combinations, Layer 4 event-risk behavior, Layer 5 alpha errors, Layer 6/7/8 position-management choices, Layer 9 option-expression drag, and event/co-event explanations.

Layer 10 owns the temporal-attention promotion staging loop inside the same attribution run. It writes event-focus proposals, deterministic temporal-attention candidate rows, same-family occurrence scans, bias-association packets, event-strategy promotion reviews, and any accepted temporal-attention pool entries as Layer 10 artifacts. Co-event/confounder, point-in-time leakage, base-rate/control, and association-strength gates are deterministic. Codex CLI, when invoked, is a final `event-strategy-promotion-review` guard over a compact packet only; it must not calculate the base gates, call providers, activate models, or mutate broker/account/order state.

Layer 10 must separate model failure time from impact exposure time. Event attribution uses `impact_exposure_time`, the earliest known time the adverse or missed impact began to appear, as the causal cutoff; `decision_time` is only a marked fallback and cannot pass the deterministic temporal-attention gate by itself. Impact severity is target-normalized when possible using expected move, volatility, ATR, or an equivalent target context, because the same raw move can represent different severity across instruments.

Event-family packets do not have to prove a linear directional relationship. Layer 10 treats pre-release and post-release evidence as two phases of the same event lifecycle. Before formal release, earnings, filings, guidance, and scheduled macro releases describe point-in-time risk-state change when the event appears; they are not predictions of the undisclosed result. After the release is available point-in-time, the same event family enters the post-release impact stage. Accepted packets hand Layer 4 a phase-aware state overlay such as `event_pre_release_risk_state_change` or `event_post_release_impact_state` for downstream state composition.

## Dashboard Refresh Events

The resident service triggers the storage-owned dashboard read-model refresh whenever it writes workflow-state progress, including stage-start transitions. The storage refresh timer remains a fallback calibration route; it is not the primary dashboard progress path.

## Progress Stall Guard

Historical automation must not sit in an apparently running but non-advancing state. The resident daemon treats ten minutes without executed scheduler progress as `scheduler_progress_stalled` and opens a server-wide agent error handoff for diagnosis/repair. Stage execution has the same ten-minute active-progress guard: if a running child process stops updating its task-progress file, the executor terminates the stage, records `stage_progress_stalled`, and routes it through the agent repair path. Waiting for a future incomplete calendar fold is the only normal no-progress exception.
