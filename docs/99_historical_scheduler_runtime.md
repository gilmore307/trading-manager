# Historical Scheduler Runtime

`trading-manager` treats historical-data model training as a maintained system-service runtime, not a manual script sequence. The canonical owner is the historical scheduler service; chat/manual CLI runs are debugging and recovery tools only. The runtime goal is continuous progress with hard safety gates where they still belong: provider calls run autonomously under manager request/resource/coverage controls, model activation is approved or deferred by the agent through `agent_model_promotion_decision_v1`, storage lifecycle mutation is rule-executed through lifecycle policy plus protected-set checks and receipts, and broker/order/fill/account mutation remains execution-owned.

## Runtime Shape

The persistent entrypoint is:

```bash
PYTHONPATH=src python3 scripts/tasks/run_automation_scheduler_daemon.py \
  --start-month 2016-01 \
  --end-month 2016-01 \
  --execute-safe-preparation \
  --execute-safe-offline-stages \
  --execute-autonomous-provider-stages \
  --auto-select-next-work \
  --advance-month-on-complete
```

The daemon audits month-scoped workflow checkpoints to identify the earliest open month, or the next chronological month after the latest completed checkpoint, then repeatedly calls the capacity-aware scheduler tick. It re-applies that automatic work selection before each tick, so provider dispatches, repair runs, or smoke runs that complete months while the daemon sleeps are folded back into the resident cursor instead of making the service walk one already-complete month per interval. Each tick writes a checkpoint, appends one decision JSONL row, uses a single-instance lock so two historical schedulers do not race each other, and advances the month cursor when a month reaches terminal workflow completion.

## Durable Runtime Files

Default local runtime files live under ignored `storage/runtime/`:

| File | Contract | Purpose |
| --- | --- | --- |
| `historical_scheduler_state.json` | `manager_scheduler_daemon_state_v1` | Resume checkpoint: tick counters, last decision, last internal stage, last error, service-management markers, automatic work-selection evidence, and current month scope. |
| `historical_scheduler.lock` | lock file | Single-instance guard; stale locks may be replaced only when the recorded process is gone and the lock is old. |
| `historical_scheduler_decisions.jsonl` | `manager_scheduler_decision_v1` rows | Append-only operational log for scheduler decisions and gate outcomes. |
| `model_training_workflow_state_YYYY-MM.json` | `manager_model_training_workflow_state_v1` | Month-scoped workflow checkpoint that the service uses for automatic next-work selection and resume. |

These files are runtime state, not Git artifacts. If the daemon restarts after host reboot or process failure, it resumes from the checkpoint and re-enters the scheduler work loop instead of relying on chat/session memory.

## Status and Readiness Surface

The read-only status entrypoint is:

```bash
PYTHONPATH=src python3 scripts/tasks/inspect_historical_scheduler_status.py
```

It emits `manager_historical_scheduler_status_v1` and performs no provider calls, no model activation, no broker execution, and no storage lifecycle mutation. The status row summarizes:

- service template/env/wrapper readiness and required service flags;
- lock state (`absent`, `active`, or `stale`);
- selected current month from daemon state or automatic checkpoint selection;
- current workflow stage, blocked reason, and latest scheduler decision;
- provider dispatch posture, latest provider-call accounting, and dispatch flag;
- local failure evidence files/rows for failure-register review;
- explicit gated-scope states for provider acquisition, model activation, storage lifecycle mutation, and broker/account mutation;
- recommended next operator action, such as enabling the service, observing logs, or clearing a stale lock.

This status surface is the normal observation tool after service activation. It exists so operators do not need to infer scheduler health by manually chaining workflow commands.

## Boot and Supervision

Reviewed host templates live in `deploy/`:

- `deploy/systemd/trading-manager-historical-scheduler.service`
- `deploy/systemd/trading-manager-historical-scheduler.env`
- `deploy/logrotate/trading-manager-historical-scheduler`

The systemd service is the canonical runtime owner. It is designed for `Restart=always` and `WantedBy=multi-user.target`, giving process supervision and boot autostart after an operator installs/enables it. The unit runs with automatic next-work selection, safe preparation, bounded autonomous provider-stage dispatch/reconcile, safe offline stage execution, and chronological month-cursor advancement enabled. Committing the template does not install or enable the service on this host.

Example operator flow after review:

```bash
sudo cp deploy/systemd/trading-manager-historical-scheduler.service /etc/systemd/system/
sudo cp deploy/systemd/trading-manager-historical-scheduler.env /etc/default/trading-manager-historical-scheduler
sudo systemctl daemon-reload
sudo systemctl enable --now trading-manager-historical-scheduler.service
sudo systemctl status trading-manager-historical-scheduler.service
```

Do not enable the service until the active host path, Python path, scheduler flags, resource policy, and provider/model/storage gate posture have been reviewed. Once enabled, do not drive the normal historical workflow by chat/manual script chains; use manual CLI only for inspection, repair, smoke tests, or emergency intervention.

## Maintenance Guarantees

The historical scheduler runtime must provide:

- **Residency:** the daemon is a long-running process supervised by a host service manager when enabled; this is the normal production control path, not an optional convenience.
- **Checkpoint/restart:** every tick updates `manager_scheduler_daemon_state_v1`; restart resumes from the latest checkpoint and current month cursor.
- **Single-instance safety:** the lock prevents duplicate daemon loops from racing on the same task payloads and state.
- **Observable decisions:** every tick appends one decision row for review of ready/backoff/executed/error outcomes, and `inspect_historical_scheduler_status.py` summarizes the current service posture without mutating runtime state.
- **Resource protection:** host resource gates still run on every tick. Market-hours protection is configurable; in the current pre-promotion full-training phase `TRADING_MANAGER_MARKET_HOURS_PROTECTION_ENABLED=false` disables market-hours backoff because no production model/live trading capacity is active yet.
- **Gate preservation:** provider calls run only through bounded manager dispatch; model activation, storage lifecycle mutation, and broker execution remain blocked unless their explicit gates are satisfied.
- **Automatic work selection:** on service start and before every tick, the daemon reviews completed/open month-scoped workflow states, resumes the earliest open month if one exists, otherwise selects the next chronological month after the latest completed checkpoint; the owner does not have to say where to continue, and externally completed months are skipped on the next service tick.
- **Chronological cursor:** terminal month completion advances the daemon to the next YYYY-MM month under the chronological-forward policy.
- **Recoverability:** runtime logs/state are local operational evidence; canonical provider/model receipts still belong in manager/storage contracts as those stages are implemented.
- **Explicit deferred scopes:** production model activation, storage lifecycle mutation, and broker/order/fill/account mutation are visible as gated statuses rather than hidden scheduler todos.

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

`advance_model_training_workflow.py` refreshes this state, ingests component receipts with `manager_stage_id` / `stage_id`, records receipt/review references for provider stages, and selects the next ready or gated stage. For component-local receipts that do not embed a manager stage id, use `--stage-receipt STAGE_ID=PATH`; manager attaches receipt/artifact evidence but does not mark the stage complete until expected successful receipt coverage is met. Scheduler decisions include both the static graph and durable state so resident operation can resume after restarts.

Current execution still preserves gates: when Layer 1 or Layer 2 task keys exist, the corresponding data-acquisition stage uses autonomous historical provider acquisition under manager request, resource, receipt, and terminal-coverage controls. With `--execute-autonomous-provider-stages`, the daemon executes at most one bounded provider-dispatch/reconcile slice per tick, then writes control-plane coverage/workflow evidence before moving on. It still does not perform broker/order/account mutation or model activation. Storage lifecycle mutation remains outside the historical provider path and must follow the accepted lifecycle policy, protected-set checks, quarantine/recheck rules when applicable, and storage receipts.

`dispatch_provider_acquisition.py` is the autonomous Alpaca-bars dispatch adapter for Layer 1 and Layer 2. It prepares bounded request sets selected by `--model-layer`, prints the exact trading-data commands in plan-only mode, and performs provider calls only when `--execute-provider-calls` is present. Use repeated `--symbol`, repeated `--request-id`, or `--limit` for controlled small-batch measurement before running a full request set. After receipts exist, `reconcile_provider_stage.py` performs the safe offline closeout: discovers existing completion receipts, normalizes manager control-plane rows, proposes/persists failed receipts as `agent_review_required` failure-register facts when requested, refreshes stage coverage, and can ingest the written coverage report into workflow state. It never dispatches providers or bypasses coverage gates.

`execute_model_training_stage.py` handles the other side of the loop: it executes one ready safe offline stage, writes stdout/stderr logs and a `component_completion_receipt_v1`, updates workflow state when requested, and refuses Layer 1/2 provider-dispatch stages. The scheduler/daemon expose `--execute-safe-offline-stages` to admit at most one non-provider offline stage per tick after market/resource gates pass; provider stages are routed through `--execute-autonomous-provider-stages` instead.

For `layer_01_market_regime.feature_generation`, the safe offline command first materializes already-acquired `01_feed_alpaca_bars` `equity_bar.csv` artifacts into `trading_data.source_01_market_regime`, then generates `trading_data.feature_01_market_regime`. This stage is allowed to write deterministic SQL source/feature rows, but it must keep `provider_calls=0`, `model_activation_performed=false`, and `broker_execution_performed=false`. Known accepted no-data symbols stay represented by failure-register rows rather than fabricated bars.

Layer 2 data-acquisition preparation now reuses the same request/payload/handoff/provider-dispatch path for the reviewed sector/industry ETF universe. Stage coverage matches Layer 1 and Layer 2 Alpaca-bar rows by reviewed universe/request id, not by month alone, so the two panels cannot contaminate each other's coverage counts. Reviewed preflight `accepted_skip` rows for known not-yet-listed instruments count as terminal reviewed skips, not as ready output, and downstream remains blocked until ready outputs plus reviewed skips cover the expected stage count. Preparation, coverage review, and workflow refresh still make no provider calls; provider calls occur through the autonomous provider-dispatch path.

For `layer_02_sector_context.feature_generation`, the safe offline command first materializes already-acquired `01_feed_alpaca_bars` `equity_bar.csv` artifacts into the shared `trading_data.source_01_market_regime` bar table, then generates `trading_data.feature_02_sector_context`. Like Layer 1 feature generation, this deterministic stage must keep `provider_calls=0`, `model_activation_performed=false`, and `broker_execution_performed=false`.

The resident scheduler/service-control boundary is closed enough for supervised operation. Broader component execution coverage beyond the Alpaca-bars adapter is future provider-extension work and must start from concrete source-ready evidence plus the same dispatch/reconcile contracts. Artifact discovery for component receipts now captures final outputs and supporting step references; richer component-specific indexing belongs with each new component adapter rather than as an open scheduler bypass.
