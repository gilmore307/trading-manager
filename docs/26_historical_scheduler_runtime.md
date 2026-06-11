# Historical Scheduler Runtime

The historical scheduler is the resident no-broker service for historical modeling progress.

## Boundary

The service may supervise:

- request planning;
- provider-dispatch stages under explicit controls;
- feature/input preparation;
- safe offline model/evaluation stages;
- reusable foundation substrate preparation;
- target-specific substrate preparation;
- live-flow replay dataset preparation, one-shot replay acquisition under provider controls, dataset freeze, signal-triggered replay option-feature repair, and replay dispatch;
- post-replay failure-attribution request preparation;
- promotion-review packet preparation;
- status and dashboard payload generation.

The service must not perform broker/order/fill/account mutation, production model activation, or active promoted-model roster selection.

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

Progress stall guard: the daemon uses `TRADING_MANAGER_SCHEDULER_PROGRESS_STALL_SECONDS=600` by default. If no executed progress is observed for that window, it writes a `scheduler_progress_stalled` server-error handoff and invokes the configured agent repair runner. Stage subprocesses also use `TRADING_MANAGER_STAGE_PROGRESS_STALL_SECONDS=600` by default and must keep their active task-progress file fresh while running.

Agent repair closure is a separate internal service. `trading-manager-agent-repair-closure.timer` runs `scripts/tasks/close_agent_repairs.py` every minute. The closure controller scans completed server-error diagnoses, refuses broker/account/order/fill/position/buying-power/funds scopes, pushes already-committed internal repo repairs, restarts internal services when the diagnosis requires it, triggers dashboard refresh, and writes `agent_repair_closure_receipt.json`. This controller is the manager-owned handoff after agent repair; agent diagnosis alone is not considered closed-loop completion.

Replay dataset closure is part of the daemon lifecycle, not a manual side path.
After a fold completes M01-M06 model generation, the daemon runs
`model_group.replay_dataset` before `model_group.replay`. That worker writes the
fold-bound background/target/event context when missing, calls the
evaluation-owned dataset preparation script, runs bounded one-shot replay
acquisition only when `--execute-autonomous-provider-stages` is enabled,
refreshes coverage, and freezes the dataset once local coverage is complete. It
must report safety flags for provider calls, SQL mutation, model training, model
activation, broker execution, and account mutation on every decision.

Replay option-feature closure is also part of the daemon lifecycle, but it is
not a pre-replay scan. The daemon runs `model_group.replay` first so the replay
clock advances through the current component graph using only point-in-time
evidence. If replay emits an M05 option-expression signal and lacks the matching
point-in-time candidates, replay backs off with
`model_group_replay_option_feature_acquisition_required`; the daemon then runs
`model_group.replay_option_features` only for the emitted sample timestamps,
prepares the matching regular-session option-chain source day windows, dispatches
bounded historical ThetaData calls only when
`--execute-autonomous-provider-stages` is enabled, generates M05 features from
`trading_data.option_chain_state_source`, and retries replay from the same
lifecycle. If the bounded provider request deterministically reports unavailable
source data, the daemon records a `snapshot_type = source_unavailable` sentinel
row in `trading_data.model_05_option_expression_feature_generation` for that signal
timestamp so replay can continue through a no-option expression path instead of
repeating the same provider request. It must not derive option downloads from
all equity bars, and it must not perform broker/order/fill/account mutation,
production model activation, or promoted-roster changes.

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

Provider dispatch may create live-enabled runtime task-key copies only as subprocess input. Successful dispatch removes those runtime copies after the provider command consumes them. Failed dispatch retains them as bounded diagnostic evidence. The prepared source task key remains the canonical request artifact.

## Normal Inspection

```bash
PYTHONPATH=src python3 scripts/tasks/inspect_historical_scheduler_status.py
PYTHONPATH=src python3 scripts/tasks/build_historical_task_progress_summary.py
```

## Current Priority

Reusable foundation catch-up remains first. Runtime advances exactly one
canonical month during this phase after reusable M01 background-context
data/feature substrate and fold-scoped M03 event-state observation inputs are
complete. M03 event substrate is collected each fold because accepted event
families and M06-governed event attributes may differ across folds.

Target-specific substrate work is the second phase. It prepares M02 target
state, target-local evidence, M05 option-expression inputs when applicable, and
other target-scoped source/feature rows only when a downstream run needs them.
Target-substrate checkpoints are data-preparation state, not parallel public
task lanes; they do not force replay to trade that target.

Fold progression is serial. After a fold finishes M01-M06 model work, the
scheduler holds the fold lane until model replay, residual-event governance
attribution, model evaluation, model promotion, and maintenance/readiness
handoff complete. It must not start the next fold or rotate to another target
while that model-group lifecycle is still open.

Replay is run-cycle scoped. It simulates the frozen live component graph against the historical point-in-time candidate pool, allowing components to choose no target, one target, or a target combination. Replay does not start from a preselected symbol except in explicit diagnostic repair scenarios.

Failure attribution is a separate task between replay and evaluation. M06
residual-event governance starts at this boundary for settled replay evidence
and must not run as a pre-replay provider input stage. Attribution may inspect
target selection misses, portfolio combinations, event/co-event explanations,
underlying-vs-option failure locus, option-expression drag, and
overblock/underblock behavior.

Evaluation consumes replay and attribution evidence. Promotion review must wait for the candidate bundle's replay, attribution, and evaluation evidence; single-layer checks and target-substrate runs remain diagnostic until the full run cycle closes.

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
