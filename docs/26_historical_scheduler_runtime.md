# Historical Scheduler Runtime

The historical scheduler is the resident no-broker service for historical modeling progress.

## Boundary

The service may supervise:

- request planning;
- provider-dispatch stages under explicit controls;
- feature/input preparation;
- safe offline model/evaluation stages;
- Layer 9 residual event-risk evidence preparation;
- promotion-review packet preparation;
- status and dashboard payload generation.

The service must not perform broker/order/fill/account mutation or production model activation.

## Service Shape

Reviewed service templates live under `deploy/`. Runtime state lives under `trading-storage/storage/02_control_plane/runtime/`.

Default runtime files:

| File | Purpose |
|---|---|
| `historical_scheduler_state.json` | Resume checkpoint and latest decision context. |
| `historical_scheduler.lock` | Single-instance daemon guard. |
| `historical_scheduler_decisions.jsonl` | Append-only scheduler decisions. |
| `model_training_workflow_state_YYYY-MM.json` | Month-scoped workflow checkpoint. |
| `source_existing_bootstrap/latest.json` | Evidence for preserved source coverage. |

Workflow-state writes emit a dashboard refresh event when `TRADING_MANAGER_DASHBOARD_REFRESH_ON_WORKFLOW_STATE_WRITE=true`. The event starts the storage-owned read-model refresh service with `--no-block`, so WebSocket subscribers see newly materialized dashboard snapshots immediately after state transitions while the 5-second storage timer remains a fallback.

## Lock Contract

Schema: `schemas/scheduler_lock.schema.json`.

The scheduler uses stable lock identities before increasing concurrency. Locks are coordination contracts, not authorization to call providers, mutate storage lifecycle, activate models, or touch broker/account state. Dry-run scheduler decisions and read-only scheduler status include `scheduler_lock_plan` so operators can see the required daemon/stage/provider/reconcile lock lanes before any worker launch. Execution paths now acquire local file-backed locks for month/stage writes, provider partition dispatch, provider-stage reconcile, and persisted model-promotion request lanes.

| Scope | Key shape | Owner |
|---|---|---|
| `daemon` | `lock:daemon:historical_scheduler` | One process-level service instance. |
| `month_stage` | `lock:stage:<month>:<stage_id>` | One workflow transition lane for a month/stage. |
| `provider_partition` | `lock:provider:<month>:<stage_id>:<provider_id>:<partition_id>` | One provider worker partition; writes partition receipts only. |
| `reconcile` | `lock:reconcile:<month>:<stage_id>` | One receipt reconciliation and stage-state transition. |
| `promotion` | `lock:promotion:<model_id>:<candidate_ref>` | One model promotion candidate review lane. |

Provider workers must not directly advance terminal workflow state. They write partitioned receipts; the reconcile lane owns stage coverage and workflow-state transitions.

## Normal Inspection

```bash
PYTHONPATH=src python3 scripts/tasks/inspect_historical_scheduler_status.py
PYTHONPATH=src python3 scripts/tasks/build_historical_task_progress_summary.py
```

## Current Priority

Layer 1/2 foundation catch-up remains first. A month can advance during this phase after reusable data-acquisition and feature-generation substrate is complete. After the target and fold are fixed, the scheduler may run a second acquisition/feature phase for independent target/fold evidence, such as event-library-driven Layer 4 event evidence, but those stages must obey the contract in `docs/03_contracts.md`: `data_acquisition` downloads or snapshots source evidence, and `feature_generation` derives deterministic features from that source evidence without reading model outputs. Anything that requires an upstream model output must be a separate model-dependent task/table with explicit blockers, not a source feature.

Model generation is fold-scoped. Once a target-scoped Model Worker fold is opened, that fold owns the target lane until it reaches a terminal state; a blocked open fold must not be skipped and later folds must not receive prefetch/substrate work. This preserves Layer 10 event-governor causality: each fold may update event-focus evidence that should shape subsequent fold acquisition and interpretation. Layer-local `model_evaluation` stages are internal artifact checks and failure-attribution evidence only; the owner-facing Evaluation task is the model-group replay over the accepted out-of-sample window. Promotion review is fold-scoped, but it must wait until the full Layer 1 through Layer 10 stack has completed internal checks and model-group replay evidence exists; single-layer fold results are diagnostic until the full stack closes.

## Safety Evidence

Status surfaces should explicitly show:

```text
provider_calls
model_activation_performed
storage_lifecycle_mutation_performed
broker_execution_performed
lock_state
lock_plan
selected_month
selected_stage
latest_decision
recommended_operator_action
```

## Recovery Rule

Restarting the service should resume from durable runtime state. Deleted manager request/receipt rows must not force valid already-downloaded source inputs to be redownloaded; source-existing bootstrap should reseed coverage when point-in-time evidence exists.
