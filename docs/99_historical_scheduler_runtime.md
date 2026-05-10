# Historical Scheduler Runtime

`trading-manager` treats historical-data model training as a maintained background runtime, not a manual script sequence. The runtime goal is continuous progress with hard safety gates: provider calls require `live_call_approval_v1`, model activation requires an approving `review_decision_v1`, and broker/order/fill/account mutation remains execution-owned.

## Runtime Shape

The persistent entrypoint is:

```bash
PYTHONPATH=src python3 scripts/tasks/run_automation_scheduler_daemon.py \
  --start-month 2016-01 \
  --end-month 2016-01 \
  --execute-safe-preparation
```

The daemon repeatedly calls the capacity-aware scheduler tick, writes a checkpoint after every iteration, appends one decision JSONL row per tick, and uses a single-instance lock so two historical schedulers do not race each other.

## Durable Runtime Files

Default local runtime files live under ignored `storage/runtime/`:

| File | Contract | Purpose |
| --- | --- | --- |
| `historical_scheduler_state.json` | `manager_scheduler_daemon_state_v1` | Resume checkpoint: tick counters, last decision, last internal stage, last error, and month scope. |
| `historical_scheduler.lock` | lock file | Single-instance guard; stale locks may be replaced only when the recorded process is gone and the lock is old. |
| `historical_scheduler_decisions.jsonl` | `manager_scheduler_decision_v1` rows | Append-only operational log for scheduler decisions and gate outcomes. |

These files are runtime state, not Git artifacts. If the daemon restarts after host reboot or process failure, it resumes from the checkpoint and re-enters the scheduler work loop instead of relying on chat/session memory.

## Boot and Supervision

Reviewed host templates live in `deploy/`:

- `deploy/systemd/trading-manager-historical-scheduler.service`
- `deploy/logrotate/trading-manager-historical-scheduler`

The systemd service is designed for `Restart=always` and `WantedBy=multi-user.target`, giving process supervision and boot autostart after an operator installs/enables it. Committing the template does not install or enable the service on this host.

Example operator flow after review:

```bash
sudo cp deploy/systemd/trading-manager-historical-scheduler.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now trading-manager-historical-scheduler.service
sudo systemctl status trading-manager-historical-scheduler.service
```

Do not enable the service until the active host path, Python path, scheduler flags, resource policy, and approval-gate posture have been reviewed.

## Maintenance Guarantees

The historical scheduler runtime must provide:

- **Residency:** the daemon is a long-running process supervised by a host service manager when enabled.
- **Checkpoint/restart:** every tick updates `manager_scheduler_daemon_state_v1`; restart resumes from the latest checkpoint.
- **Single-instance safety:** the lock prevents duplicate daemon loops from racing on the same task payloads and state.
- **Observable decisions:** every tick appends one decision row for review of ready/backoff/executed/error outcomes.
- **Resource protection:** market-hours and host resource gates still run on every tick.
- **Gate preservation:** provider calls, model activation, and broker execution remain blocked unless their explicit gates are satisfied.
- **Recoverability:** runtime logs/state are local operational evidence; canonical provider/model receipts still belong in manager/storage contracts as those stages are implemented.

## Current Full-Stack Workflow Graph

The daemon now carries a manager-owned `manager_model_training_workflow_plan_v1` for all eight model layers plus a durable `manager_model_training_workflow_state_v1` checkpoint. Each layer has explicit stages for data acquisition, feature/input preparation, model generation, model evaluation, promotion-review preparation, and maintenance. Layers 5-7 intentionally mark trading-data feature generation as `not_applicable` because their inputs are upstream model/control-plane/position-risk artifacts rather than new provider data surfaces.

The workflow is intentionally not a synchronized all-layers-per-month loop:

| Segment | Progression policy |
| --- | --- |
| Layer 1 | Fixed market/cross-asset panel; continue chronological months independently after each month is complete. |
| Layer 2 | Fixed sector/industry panel; continue chronological months once Layer 1 context exists, without waiting for downstream layers. |
| Layers 3-7 | Target-major serial chain; for one selected target candidate, complete Layers 3 -> 4 -> 5 -> 6 -> 7 before admitting the next target candidate unless a reviewed coverage exception is recorded. |
| Layer 8 | Option-expression expansion begins only after the upstream Layer 1-7 context/target chain is complete for the selected target. |

This preserves the finite-panel nature of Layers 1-2 while preventing the open Layer 3+ candidate space from exploding into unbounded parallel target/contract expansion.

`advance_model_training_workflow.py` refreshes this state, ingests component receipts with `manager_stage_id` / `stage_id`, records reviewed approval references for gated stages, and selects the next ready or approval-blocked stage. For component-local receipts that do not embed a manager stage id, use `--stage-receipt STAGE_ID=PATH`; manager attaches receipt/artifact evidence but does not mark the stage complete until expected successful receipt coverage is met. Scheduler decisions include both the static graph and durable state so resident operation can resume after restarts.

Current execution still preserves gates: when Layer 1 or Layer 2 task keys exist, the corresponding data-acquisition stage becomes approval-blocked with `approval_gate_required=live_call_approval_v1`. The daemon does not perform provider calls, model activation, or broker execution until the corresponding reviewed gate is implemented and satisfied.

`dispatch_approved_provider_acquisition.py` is the approved Alpaca-bars dispatch adapter for Layer 1 and Layer 2. It validates `live_call_approval_v1` against the prepared request set selected by `--model-layer`, prints the exact trading-data commands in plan-only mode, and only performs provider calls when `--execute-approved-provider-calls` is present. Use repeated `--symbol`, repeated `--request-id`, or `--limit` for controlled small-batch measurement before running a full approved request set. Successful component receipts can then be ingested by `advance_model_training_workflow.py` to unlock downstream offline feature/model/evaluation stages.

`execute_model_training_stage.py` handles the other side of the loop: it executes one ready safe offline stage, writes stdout/stderr logs and a `component_completion_receipt_v1`, updates workflow state when requested, and refuses approval-gated provider stages. The scheduler/daemon expose `--execute-safe-offline-stages` to admit at most one such stage per tick after market/resource gates pass.

For `layer_01_market_regime.feature_generation`, the safe offline command first materializes already-acquired `01_feed_alpaca_bars` `equity_bar.csv` artifacts into `trading_data.source_01_market_regime`, then generates `trading_data.feature_01_market_regime`. This stage is allowed to write deterministic SQL source/feature rows, but it must keep `provider_calls=0`, `model_activation_performed=false`, and `broker_execution_performed=false`. Known accepted no-data symbols stay represented by failure-register rows rather than fabricated bars.

Layer 2 data-acquisition preparation now reuses the same request/payload/handoff/approval-gate path for the reviewed sector/industry ETF universe. It is currently blocked on `live_call_approval_v1`; no Layer 2 provider calls have been made by preparation or workflow refresh.

The remaining implementation boundary is broader component execution coverage beyond the Alpaca-bars adapter and richer artifact discovery from each component command.
