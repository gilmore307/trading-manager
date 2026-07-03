# Contracts

Manager contracts are concise, durable control-plane facts. They let components work independently while preserving auditability and downstream readiness.

Machine-verifiable JSON Schemas in `schemas/` are the contract authority for durable manager rows. Python helpers may normalize convenience inputs, but checked-in examples and future `--write` paths must validate against those schemas before rows are treated as durable evidence or readiness state.

## Persistence Policy

| Material | Home | Rule |
|---|---|---|
| Control-plane facts | Manager SQL | Keep ids, statuses, refs, timestamps, component ids, hashes, and readiness facts. |
| Large payloads/artifacts/logs | Storage or runtime paths | Store by reference; do not duplicate blobs into SQL. |
| Temporary scratch | Ignored runtime paths | Never treat as evidence unless promoted by receipt/artifact ref. |
| Secrets | Outside repository | Reference only by alias/registry id. |

## Core Contracts

### `manager_request`

Schema: `schemas/manager_request.schema.json`.

A manager-issued request for component work.

Required idea:

```text
request_id
request_type
component_id
repo_id
status
priority
scope/window
parameter_ref or payload_ref
created_time
```

### `input_binding`

Schema: `schemas/input_binding.schema.json`.

A durable binding between a request and the input refs it may use.

```text
request_id
input_role
input_ref
schema_ref
available_time or as_of_time
```

### `run_manifest`

Schema: `schemas/run_manifest.schema.json`.

A normalized component run summary.

```text
run_id
request_id
component_id
repo_id
status
started_time
ended_time
receipt_ref
```

### `run_step`

Optional step-level detail for long runs.

```text
run_id
step_id
step_name
status
started_time
ended_time
```

### `artifact_ref`

Schema: `schemas/artifact_ref.schema.json`.

A reference to an output artifact without copying the artifact body into SQL.

```text
artifact_id
run_id
artifact_role
artifact_uri
schema_ref
content_hash or fingerprint
retention_policy
lifecycle_status
```

### `ready_signal`

Schema: `schemas/ready_signal.schema.json`.

A component or manager signal that a declared output is usable for a declared consumer scope.

```text
signal_id
request_id or run_id
ready_scope
status
producer_component
consumer_scope
evidence_ref
```

### `scheduler_lock`

Schema: `schemas/scheduler_lock.schema.json`.

A stable lock identity for historical scheduler coordination.

```text
lock_scope
lock_key
lock_path
month / stage_id / provider_id / partition_id / model_id / candidate_ref as applicable
```

Lock scopes are `daemon`, `month_stage`, `provider_partition`, `reconcile`, and `promotion`. Provider partition locks permit concurrent partition work only; reconcile locks own stage-state transitions. Dry-run decisions and status snapshots expose `scheduler_lock_plan` with the lock refs/templates required for the selected work; execution paths acquire local file-backed locks for the corresponding stage, provider partition, reconcile, and persisted promotion-request lanes.

### `model_group_rerun_plan`

Schema: `schemas/model_group_rerun_plan.schema.json`.

A dry-run-first plan for architecture-driven model group regeneration.

Required idea:

```text
plan_id
rerun_id
reason
change_origin layer + stage
affected_scope
source_data_delete required/reason/scope_refs
delete_set
protected_set
retained_set
controlled_artifact_roots
storage_lifecycle_request
scheduler_reentry_stage
expected_verification_gates
```

This contract is not a broad deletion executor. It identifies the earliest affected workflow cutpoint, computes the downstream generated-output closure, separates lifecycle candidates from protected inputs, records reusable retained artifacts, lists the controlled roots that may contain rerun intermediates, emits a `storage_lifecycle_request` bridge, and names the scheduler reentry stage. Any storage-path deletion in the plan remains subject to storage artifact-index, protected-set, quarantine/recheck, lifecycle review, and receipt gates.

## Workflow Stage Semantics

Historical workflow stages must keep source data, derived features, and model-dependent state separate.

- `data_acquisition` downloads or snapshots source evidence from an external or already-reviewed source surface. It may normalize storage paths, coverage receipts, and point-in-time source refs, but it must not derive model-informed values.
- `feature_generation` derives deterministic data features only from the acquired/source data for the same stage scope. It must be reproducible without reading another model's output, score, decision, or hidden runtime state.
- If a derived table requires any upstream model output, it is not a `feature_generation` output for that source stage. It needs a separate model/input table, an explicit model-generation stage, or a newly named intermediate task with its own contract and blockers.
- Model outputs, replay state, promotion review evidence, and maintenance surfaces must not be stored under source/feature contracts just because they are convenient downstream inputs.

For example, `trading_data.model_01_market_regime_feature_generation` is a valid feature surface when it is deterministically derived from acquired market bars. A target/event table that requires TargetStateVectorModel output, EventFailureRiskModel output, or replay portfolio state is not a feature surface under this definition.

## Label Settlement Contract

All historical model tasks use the same label-settlement clock discipline. A
row belongs to a fold or split by the time the row was observed or the decision
would have been made, not by the time its future outcome label becomes known.
Declared forward labels may acquire market data beyond the row's split or fold
window when the label horizon requires it. Boundary rows are not rejected merely
because their label settles later.

Each supervised or evaluated row must keep these clocks separate when the data
is available:

```text
observed_at or decision_time
feature_available_at
label_horizon
label_end_at
label_available_at
training_cutoff
```

Training eligibility is controlled by settlement, not by row ownership:

```text
row ownership = observed_at / decision_time in the split or fold scope
label acquisition = declared forward horizon, even when it crosses the window
training eligibility = label_available_at <= training_cutoff
leakage audit = feature_available_at and label_available_at timing checks
```

For example, an event observed on `2016-12-29` in the `fold_aapl_2016`
training period remains a 2016 training-period event row. If its declared
10-trading-day risk label settles in January 2017, manager may acquire the
January market data needed for that label. The row can be used only by training
or evaluation runs whose `training_cutoff` is after `label_available_at`; it
must not be treated as known by a model snapshot whose cutoff preceded label
settlement.

## Train Replay Realtime Input Parity

`docs/29_train_replay_realtime_input_parity.md` owns the cross-phase model-input
parity contract. Training, replay, and realtime may resolve different physical
artifacts or refs, but model decision inputs must share the same semantic input
families, registry terms, source identities, feature/vector definitions,
point-in-time clock rules, freshness/quality rules, fallback states, and
governance status.

This parity contract applies to model decision inputs only. Realtime execution
guardrails such as broker/account state, halt checks, restrictions, and kill
switches may be broader than trained model inputs, but they must not be
represented as trained model signals unless accepted by the normal model
governance route.

## Model Group Rerun Semantics

A model group rerun is a controlled invalidation and scheduler reentry operation used when an architecture, contract, schema, feature, source-scope, or execution-route change makes existing generated outputs stale. It is also a storage lifecycle trigger: stale downstream artifacts enter the storage lifecycle system as candidates, not as manager-owned deletion instructions.

Rerun planning uses the earliest affected `layer.stage` cutpoint:

```text
layer_XX.data_acquisition
layer_XX.feature_generation
layer_XX.model_generation
layer_XX.model_evaluation
layer_XX.replay_execution
layer_XX.replay_review
layer_XX.post_replay_attribution
layer_XX.fold_settlement
layer_XX.promotion_review
layer_XX.maintenance
layer_XX.read_model_refresh
```

The planner must compute the downstream closure from that cutpoint and produce `delete_set`, `protected_set`, `retained_set`, `controlled_artifact_roots`, and `storage_lifecycle_request`. `delete_set` is a compatibility field for rerun-invalidated lifecycle candidates; it is not physical deletion authority. It may include generated SQL rows, features, model outputs, model artifacts, replay outputs, attribution outputs, evaluation evidence, promotion-review evidence, read models, runtime state, and workflow completion state. Completed workflow state after the cutpoint may be invalidated so the scheduler does not skip the rerun. Durable artifacts and physical files enter storage lifecycle classification, where storage decides whether to retain, compress, archive, quarantine, or delete. Reusable upstream files that remain valid, such as already-acquired source data, belong in `retained_set` so inherited artifacts stay controlled instead of becoming unexplained leftovers.

Source data is protected by default. It enters `delete_set` only when the cutpoint is `data_acquisition` and the task's required source data changed, the acquisition contract changed, the provider/source parameters changed, or the existing source partition is confirmed wrong, incomplete, duplicated, contaminated, or scoped to an obsolete experiment. When the cutpoint is `feature_generation` or later, source data remains in `protected_set` even if all downstream artifacts are rebuilt.

Candidate scope must be the smallest affected scope: provider/source, target symbol, fold or month window, timeframe, artifact family, and contract/schema. A rerun plan must not use broad "delete everything after this layer" language without concrete refs.

Execution order is lifecycle classification request first, bounded workflow-state invalidation second, durable reset receipt third, then scheduler reentry from the cutpoint through the current model-group lifecycle. Physical file deletion is a later storage lifecycle action after artifact index, protected-set clearance, quarantine/recheck, reviewed decision, and deletion receipt. Only one scheduler daemon may own a rerun scope at a time.

## Fold Maintenance Data Disposition

Fold maintenance classifies data by reuse and evidence value before storage
lifecycle handling. It must not treat every file written during a fold as part
of that fold's disposable workspace.

Disposition is not a fold-close judgment call. Every fold artifact writer must
emit or imply one of the accepted disposition classes when the artifact is
created. Maintenance applies the class; it does not rediscover the artifact's
business purpose from path names.

The disposition classes are:

```text
protected_foundation_reusable
protected_canonical_source
protected_long_term_knowledge
retained_evidence_summary
retained_manifest_only
retained_candidate_model
compress_or_archive_candidate
delete_after_fold_settlement
rolling_retention_side_product
blocked_pending_storage_lifecycle_review
```

Each fold-scoped artifact classification must record:

```text
disposition_class
reuse_scope = foundation | canonical_source | long_term_knowledge | fold | target_fold | replay_run | side_product
producer_stage_id
fold_id or global_scope_ref
consumer_refs
source_refs or parent_artifact_refs
retained_summary_refs
cleanup_candidate_refs
protection_reason
```

At fold settlement, maintenance writes a `fold_maintenance_manifest` with every
artifact family below grouped by disposition class. Missing classification is a
blocker: unclassified artifacts enter `blocked_pending_storage_lifecycle_review`
and must not be deleted by default.

Deletion eligibility is consumer-aware. If an artifact is referenced by any
open or future fold, replay dataset, replay run, evaluation, promotion,
dashboard, repair, or accepted source/knowledge contract, maintenance must keep
the canonical artifact and mark the fold-local cleanup request as retained due
to active consumers. A fold may not delete data needed by the 2021-2026 replay
window just because that fold has settled.

The 2021-2026 replay input substrate is shared, protected data. Background
market data, M01 reusable context inputs, M03 event data, calendar/session data,
market-control data, and other model-input source partitions used by replay are
stored once in canonical shared/source locations and reused by every fold's
replay. Fold-specific replay manifests may cite those refs, but they must not
create duplicate private copies of identical source payloads.

The fixed fold disposition matrix is:

| Artifact family | Examples | Disposition after fold settlement |
|---|---|---|
| M01 reusable foundation source | Broad market bars, cross-asset controls, macro/calendar source partitions used by M01 background/context | `protected_foundation_reusable`; keep for future targets and folds. |
| M01 reusable foundation features and manifests | M01 market/background feature rows, feature-ready manifests, source coverage evidence, training-problem identity | `protected_foundation_reusable`; keep unless superseded by a rerun or accepted contract retirement. |
| Canonical shared source data | Reusable provider/source partitions under the shared source layout, including reusable target bars, ETF controls, peer bars, option source partitions, SEC/news/calendar source, and canonical market-data dependency fetches | `protected_canonical_source`; future folds reuse it instead of redownloading. |
| Replay shared input substrate | 2021-2026 replay background/context inputs, M01/M03 replay-consumed source refs, canonical event/calendar/session source, reusable market/sector/peer controls, fixed replay candidate-universe source refs | `protected_canonical_source` or `protected_foundation_reusable`; keep while any replay dataset/run/evaluation/promotion can cite it, and store it once rather than duplicating per fold. |
| Non-reacquirable or long-term event knowledge | Trading Economics protected source, accepted M03 event ontology, event-family/dossier lineage, reviewed event-modelability packets, accepted temporal/event-focus evidence | `protected_long_term_knowledge`; keep concise provenance and current canonical evidence. |
| Fold-scoped branch downloads | AAPL fold temporarily fetched NVDA/QQQ/SMH/peer data for event-scope controls, label settlement, replay diagnostics, or repair, where the partition was not promoted to canonical source coverage and has no other consumer | `delete_after_fold_settlement` after retaining dependency reason, source refs, coverage summary, hashes, and consumer result refs. If replay or another fold still needs it, keep or promote the canonical partition and delete only duplicate fold-local copies. |
| Provider dispatch side products | Prepared task keys, consumed runtime task-key copies, repeated request manifests, provider subprocess scratch, retry-local payload copies | `rolling_retention_side_product`; keep terminal request/receipt refs and counters, remove consumed live runtime copies, roll older duplicates. |
| Progress-monitoring side products | Stage heartbeats, row-progress snapshots, local scheduler progress files, detailed run-step progress, transient debug traces | `rolling_retention_side_product`; keep final completion receipt, transition summary, counters, and error refs only. |
| Temporary scratch and repair diagnostics | One-off scratch CSV/JSON, investigation dumps, failed-run copied context, non-promoted repair artifacts | `delete_after_fold_settlement` or `rolling_retention_side_product` after the repair receipt cites the durable evidence. |
| Data-acquisition receipts and coverage summaries | Source refs, coverage summary rows, provider run receipts, hashes, source quality summaries | `retained_evidence_summary`; keep compact evidence, not duplicate source payloads. |
| Deterministic feature-generation intermediates | Rebuildable feature tables/files, intermediate joins, temporary vectorization outputs, split-local feature caches | `retained_manifest_only` when source refs, code/schema refs, hashes, row counts, and quality summaries can reproduce them; otherwise `compress_or_archive_candidate` until reproducibility is proven. |
| Label-settlement artifacts | Label horizon manifests, label availability clocks, forward-outcome summaries, eligibility rows, leakage audit summaries | `retained_evidence_summary`; large rebuildable label tables may be `compress_or_archive_candidate` after fixed summaries and hashes remain. |
| M03 event ledger and target/scope projections | Fold PIT event ledger, event-risk state for M04, market/sector/symbol residual scope projections, target exposure projections | Shared ledger and accepted ontology are protected; fold/target projections keep summaries/manifests and may compress large rebuildable projection tables. |
| Model training manifests | Training-problem manifest, feature/label refs, code/data versions, cutoff, row counts, objective, sampling, weighting, calibration input refs | `retained_evidence_summary`; mandatory for retrain/skip decisions across targets. |
| Candidate model artifacts | Final fold candidate model, selected checkpoint, calibration layer, model config used by replay/evaluation | `retained_candidate_model` through replay, evaluation, promotion, and any accepted shadow-readiness handoff; non-selected checkpoints become `compress_or_archive_candidate` or `delete_after_fold_settlement`. |
| Non-selected checkpoint clutter | Epoch checkpoints, local early-stopping candidates, duplicate model binaries, abandoned search outputs | `delete_after_fold_settlement` after selected/final checkpoint refs and training summary remain. |
| Replay dataset freeze artifacts | Replay dataset manifest, freeze receipt, replay window manifest, source contract refs, coverage summary | `retained_evidence_summary`; required for replay reproducibility. |
| Replay execution outputs | Replay receipts, decision rows, monthly summaries, equity path metrics, selected contract path refs, execution component graph refs | `retained_evidence_summary`; large step traces compress or roll unless needed for a failure row. |
| Model-specific replay downloads | One-off option snapshots or other replay-only downloads that cannot become canonical reusable source partitions | `delete_after_fold_settlement` after replay close and retained summaries, manifests, hashes, and consumer refs. |
| Replay review and attribution outputs | Failure rows, first-gap summaries, regret rows, event-attribution suboutput against the fixed M03 ledger | `retained_evidence_summary`; detailed debug traces are side products. |
| Evaluation and promotion evidence | Benchmark metrics, incumbent comparison, uncertainty/guardrail evidence, promotion eligibility decision, promotion-readiness record, advisory agent decisions | `retained_evidence_summary`; keep because fold settlement and promotion audit depend on it. |
| Dashboard/read-model cache | Latest read model, generated UI cache, historical dashboard snapshots | latest/current is retained for display; old snapshots are `rolling_retention_side_product` unless cited by an evidence receipt. |
| Workflow and scheduler state | Fold completion state, current transition ledger, lock/daemon state, decision logs, detailed checkpoint files | keep fold completion and current transition summaries; detailed checkpoint/progress files are `rolling_retention_side_product` after settlement. |
| Error-agent request/repair artifacts | Error request, diagnosis, repair receipt, verification refs, retry decision | `retained_evidence_summary` for terminal repair evidence; copied context and scratch are side products. |

Physical deletion remains storage-owned. Manager maintenance may write the
classification, protected refs, retained refs, and deletion-candidate refs, but
storage lifecycle performs protected-set checks, receipt writing, and any
mutation.

## Review and Promotion Contracts

- `manager_dataset_evidence` summarizes snapshot/split/label/eval/control-plane coverage.
- `model_promotion_review_request` asks for promotion review.
- `agent_model_promotion_decision` is advisory evidence only. Offline promotion readiness belongs to `trading-evaluation`; runtime active selection belongs to `trading-execution`.
- `agent_storage_lifecycle_decision` is required for storage lifecycle mutation.
- Agent decisions must cite a fixed workspace skill:
  `promotion-evaluation-review`, `runtime-model-lifecycle-review`, `target-context-review`, `server-error-diagnosis`, `storage-lifecycle-review`, `failure-register-review`, or `event-strategy-promotion-review`.
- Any agent comparison between models must use anonymous model labels. The agent must not know which label is new, old, active, incumbent, champion, challenger, or latest.
- Event-family promotion staging is internal to the M03 event-impact route before replay and may be consumed by replay review event attribution after replay. The accepted artifact set is `event_focus_proposals.jsonl`, `temporal_attention_candidate_pool.jsonl`, `event_family_occurrence_scan.jsonl`, `event_family_bias_association_packets.jsonl`, `event_strategy_promotion_reviews.jsonl`, and `accepted_temporal_attention_pool_entries.jsonl`. Deterministic gates decide co-event/confounder, PIT leakage, matched-control/base-rate, and bias-association status before any agent review. `event-strategy-promotion-review` is a final guard and can only accept already reviewable packets into temporal-attention pool evidence; it does not compute the deterministic gates. Event-family packets must distinguish pre-release uncertainty from post-release observed market impact, including the same event family changing phase after a formal release becomes available point-in-time. Packets may express M03 event-state state overlays such as risk-state shift or uncertainty-risk elevation without claiming a linear up/down forecast.
- M03 event taxonomy is hierarchical. Source/category and broad domain nodes are routing and prior evidence only; modelability packets use the narrowest accepted PIT-definable mechanism family, child family, or specific event dossier. Child families and dossiers must preserve parent/fallback lineage, taxonomy version, inclusion/exclusion rules, source precedence, clock rules, scope/risk-channel defaults, and evidence gates. They must not be created from hindsight returns or replay outcomes.
- M03 event-family modelability uses two program-owned contracts before Codex semantic review. `model_06_event_family_modelability_acquisition_plan` and `model_06_event_family_modelability_evidence_packet` are retained physical contract names for current artifacts, but their current lifecycle owner is M03 event impact. The acquisition plan prepares bounded provider task keys through canonical source acquisition routes and the reviewed provider dispatcher. The evidence packet groups acquired same-family or same-dossier point-in-time evidence into the packet consumed by Codex review. These stages do not judge projection mode, probability-function class, direction, magnitude, half-life, or utility delta. A single observed event is only a candidate seed; M03 cannot assign an event-family probability-function type until multiple point-in-time same-family or same-dossier observations, coverage evidence, controls, and leakage/overlap checks are available. Codex modelability skills consume the resulting evidence packet and must perform zero provider calls.
- Replay review owns post-replay event attribution as an embedded diagnostic surface. It compares replay-reviewed failures and residuals against the fixed pre-replay M03 event-impact ledger, writes event-attribution subartifacts under the replay review run, and does not create an independent M06 workflow plan, scheduler stage, provider-acquisition route, broker execution, or model activation path.
- Event-model automation is program-controlled first. Code owns acquisition scope, coverage checks, sample thresholds, point-in-time clocks, dedupe, overlap/confounder gates, retry/stop conditions, and review readiness. Codex skills are reserved for semantic analysis such as event interpretation, taxonomy judgment, modelability reasoning, and probability-function class review when deterministic code cannot reliably decide the meaning.
- `docs/31_event_impact_distribution.md` is the canonical event-impact distribution contract. It defines projection modes, probability-function classes, M03 event-impact responsibilities, replay review event-attribution responsibilities, and the program/agent boundary.

## Status Semantics

Use concise lifecycle values such as:

```text
requested | running | succeeded | failed | blocked | cancelled | ready | partial | superseded | expired | deleted
```

A status alone is not enough. Readiness requires evidence refs and a declared consumer scope.

## Boundary

A contract can authorize downstream consumption. It cannot by itself perform provider calls, storage mutation, broker/account mutation, or production activation.
