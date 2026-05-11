# Historical Scheduler Runtime

`trading-manager` treats historical-data model training as a maintained background runtime, not a manual script sequence. The runtime goal is continuous progress with hard owner-observed gates: provider calls require agent-reviewed `live_call_approval_v1` plus proposal validation, model activation requires an approving script-called `agent_model_promotion_decision_v1`, storage lifecycle mutation requires an agent lifecycle decision, and broker/order/fill/account mutation remains execution-owned.

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

`advance_model_training_workflow.py` refreshes this state, ingests component receipts with `manager_stage_id` / `stage_id`, records agent-reviewed approval references for gated provider stages, and selects the next ready or gated stage. For component-local receipts that do not embed a manager stage id, use `--stage-receipt STAGE_ID=PATH`; manager attaches receipt/artifact evidence but does not mark the stage complete until expected successful receipt coverage is met. Scheduler decisions include both the static graph and durable state so resident operation can resume after restarts.

Current execution still preserves gates: when Layer 1 or Layer 2 task keys exist, the corresponding data-acquisition stage requires an owner-observed agent-reviewed `live_call_approval_v1` plus proposal validation. The daemon may execute provider calls automatically after that bounded review/validation path, but it still does not perform broker/order/account mutation, model activation, or storage lifecycle mutation without their own agent decision artifacts.

`dispatch_approved_provider_acquisition.py` is the agent-reviewed Alpaca-bars dispatch adapter for Layer 1 and Layer 2. It validates `live_call_approval_v1` against the prepared request set selected by `--model-layer`, prints the exact trading-data commands in plan-only mode, and performs provider calls only when `--execute-approved-provider-calls` is present. Execution also requires `--approval-validation` from `validate_live_call_approval_proposal.py` or `agent_review_live_call_approval_packet.py`, proving the reviewed approval exactly matches the proposal/request set to execute. Use repeated `--symbol`, repeated `--request-id`, or `--limit` for controlled small-batch measurement before running a full approved request set. After receipts exist, `reconcile_provider_stage.py` performs the safe offline closeout: discovers existing completion receipts, normalizes manager control-plane rows, proposes/persists failed receipts as `agent_review_required` failure-register facts when requested, refreshes stage coverage, and can ingest the written coverage report into workflow state. It never dispatches providers or bypasses coverage gates.

`execute_model_training_stage.py` handles the other side of the loop: it executes one ready safe offline stage, writes stdout/stderr logs and a `component_completion_receipt_v1`, updates workflow state when requested, and refuses Layer 1/2 provider-dispatch stages. The scheduler/daemon expose `--execute-safe-offline-stages` to admit at most one such stage per tick after market/resource gates pass.

For `layer_01_market_regime.feature_generation`, the safe offline command first materializes already-acquired `01_feed_alpaca_bars` `equity_bar.csv` artifacts into `trading_data.source_01_market_regime`, then generates `trading_data.feature_01_market_regime`. This stage is allowed to write deterministic SQL source/feature rows, but it must keep `provider_calls=0`, `model_activation_performed=false`, and `broker_execution_performed=false`. Known accepted no-data symbols stay represented by failure-register rows rather than fabricated bars.

Layer 2 data-acquisition preparation now reuses the same request/payload/handoff/agent-review path for the reviewed sector/industry ETF universe. Stage coverage matches Layer 1 and Layer 2 Alpaca-bar rows by reviewed universe/request id, not by month alone, so the two panels cannot contaminate each other's coverage counts. Reviewed preflight `accepted_skip` rows for known not-yet-listed instruments count as terminal reviewed skips, not as ready output, and downstream remains blocked until ready outputs plus reviewed skips cover the expected stage count. Preparation, coverage review, and workflow refresh still make no provider calls; provider calls occur only after the owner-observed agent review/validation/dispatch path.

For `layer_02_sector_context.feature_generation`, the safe offline command first materializes already-acquired `01_feed_alpaca_bars` `equity_bar.csv` artifacts into the shared `trading_data.source_01_market_regime` bar table, then generates `trading_data.feature_02_sector_context`. Like Layer 1 feature generation, this deterministic stage must keep `provider_calls=0`, `model_activation_performed=false`, and `broker_execution_performed=false`.

The remaining implementation boundary is broader component execution coverage beyond the Alpaca-bars adapter and richer artifact discovery from each component command.
