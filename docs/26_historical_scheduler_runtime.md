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

Progress stall guard: the daemon uses `TRADING_MANAGER_SCHEDULER_PROGRESS_STALL_SECONDS=600` by default. If no executed progress is observed for that window, it writes a `scheduler_progress_stalled` server-error handoff and invokes the configured agent repair runner. The registry row `TRADING_MANAGER_SCHEDULER_PROGRESS_NONPROGRESS_REASONS` owns daemon state reason values that are known lifecycle waits or completed bounded model-group work rather than stalls. Stage subprocesses use `TRADING_MANAGER_STAGE_PROGRESS_STALL_SECONDS=600` by default and must keep their active task-progress file fresh while running.

Agent repair closure is a separate internal service. `trading-manager-agent-repair-closure.timer` runs `scripts/tasks/close_agent_repairs.py` every minute. The closure controller scans completed server-error diagnoses, refuses broker/account/order/fill/position/buying-power/funds scopes, pushes already-committed internal repo repairs, restarts internal services when the diagnosis requires it, triggers dashboard refresh, and writes `agent_repair_closure_receipt.json`. This controller is the manager-owned handoff after agent repair; agent diagnosis alone is not considered closed-loop completion.

Replay dataset closure is part of the daemon lifecycle, not a manual side path.
After a fold completes M01-M05 model generation, the daemon runs
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
`model_group.replay_option_features` only for the emitted timestamps from the
backoff payload or its full `requirements_artifact_ref`. The callable
`scripts/tasks/drain_model_group_replay_option_features.py` is the bounded
operator entrypoint for draining a large replay requirements artifact without
rerunning replay between batches. Provider acquisition remains constrained by
`--provider-stage-next-limit`, while local SQL feature repair uses the separate
`--replay-option-feature-repair-limit` / `--feature-repair-limit` batch controls
so already-local source rows can be generated in larger safe chunks. The daemon
continues draining the same requirements artifact until the option features are
ready or a provider/source backoff is reached; only then should it retry full
`model_group.replay`. On daemon restart or a later tick, an unfinished
`option_feature_requirements.jsonl` without a completed replay receipt is treated
as pending replay-owned work and is drained before replay is dispatched again. It
prepares the matching regular-session option-chain source day windows, dispatches
bounded historical ThetaData calls only when `--execute-autonomous-provider-stages`
is enabled, generates M05 features from `trading_data.option_chain_state_source`,
and retries replay from the same lifecycle. If the bounded provider request
deterministically reports unavailable source data, or completes without writing
the requested source rows, the daemon records a `snapshot_type = source_unavailable` sentinel
row in `trading_data.model_05_option_expression_feature_generation` for that signal
timestamp so replay can continue through a no-option expression path instead of
repeating the same provider request. It must not derive option downloads from
all equity bars, and it must not perform broker/order/fill/account mutation,
production model activation, or promoted-roster changes.

After replay has M05 features and selects concrete listed option contracts, the
separate `model_group.replay_contract_paths` stage prepares
`m05_option_expression_data_acquisition_contract_path` requests from those
decision rows. This selected-contract tracking source is provider-gated and
market-data-only; it writes option path rows for replay settlement, then the
daemon retries `model_group.replay` from the same lifecycle.

Replay review also participates in the same replay-owned repair loop. Before it
writes `post_replay_review_receipt`, it checks whether reviewable decision rows
have enough future outcome and return data to quantify `available_action`,
`best_available_action_by_future_outcome`, and
`regret_to_best_available`. Completed review rows also materialize
`first_gap_component`, `first_gap_mechanism`, `layer_attribution`, and a
receipt-level diagnostic summary for dashboard scanning. If required outcome
data is missing, replay review writes
`replay_review_data_requirements.jsonl` and backs off with
`model_group_replay_review_data_required`. When those requirements point to
selected option contract paths, the daemon hands them to
`model_group.replay_contract_paths` under the existing provider gates; replay
and replay review are then retried from the same lifecycle. Replay review itself
does not call providers, mutate broker/account/order state, activate models, or
expand the point-in-time candidate set.

Bounded smoke runs may use `--max-review-rows`. Those receipts must carry
`replay_review_completion_scope=bounded_diagnostic` and `max_review_rows`; they
are inspection artifacts only and must not satisfy full Replay Review, M06, or
evaluation lifecycle gates. Only `replay_review_completion_scope=full_replay_review`
with no row cap can unlock downstream stages.

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
scheduler holds the fold lane until model replay, replay review,
residual-event governance attribution, model evaluation, model promotion, and maintenance/readiness
handoff complete. It must not start the next fold or rotate to another target
while that model-group lifecycle is still open.

Replay is run-cycle scoped. It simulates the frozen live component graph against the historical point-in-time candidate pool, allowing components to choose no target, one target, or a target combination. Replay does not start from a preselected symbol except in explicit diagnostic repair scenarios.

Replay review is a separate task between replay and M06. It inspects target
selection misses, portfolio combinations, underlying-vs-option failure locus,
option-expression drag, overblock/underblock behavior, and the component-funnel
layer where replay first diverged. M06 residual-event governance starts after
replay review for event/co-event explanations and must not run as a pre-replay
provider input stage.

Evaluation consumes replay, replay-review, and attribution evidence. Promotion review must wait for the candidate bundle's replay, replay-review, attribution, and evaluation evidence; single-layer checks and target-substrate runs remain diagnostic until the full run cycle closes.

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
