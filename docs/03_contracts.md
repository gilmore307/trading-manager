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
scheduler_reentry_stage
expected_verification_gates
```

This contract is not an executor. It identifies the earliest affected workflow cutpoint, computes the downstream generated-output closure, separates deletion candidates from protected inputs, and names the scheduler reentry stage. Any storage-path deletion in the plan remains subject to storage protected-set and lifecycle review unless the affected artifact is explicitly classified as disposable runtime state by an accepted storage policy.

## Workflow Stage Semantics

Historical workflow stages must keep source data, derived features, and model-dependent state separate.

- `data_acquisition` downloads or snapshots source evidence from an external or already-reviewed source surface. It may normalize storage paths, coverage receipts, and point-in-time source refs, but it must not derive model-informed values.
- `feature_generation` derives deterministic data features only from the acquired/source data for the same stage scope. It must be reproducible without reading another model's output, score, decision, or hidden runtime state.
- If a derived table requires any upstream model output, it is not a `feature_generation` output for that source stage. It needs a separate model/input table, an explicit model-generation stage, or a newly named intermediate task with its own contract and blockers.
- Model outputs, replay state, promotion review evidence, and maintenance surfaces must not be stored under source/feature contracts just because they are convenient downstream inputs.

For example, `trading_data.m01_market_regime_feature_generation` is a valid feature surface when it is deterministically derived from acquired market bars. A target/event table that requires TargetStateVectorModel output, EventFailureRiskModel output, or replay portfolio state is not a feature surface under this definition.

## Model Group Rerun Semantics

A model group rerun is a controlled invalidation, deletion, and scheduler reentry operation used when an architecture, contract, schema, feature, source-scope, or execution-route change makes existing generated outputs stale.

Rerun planning uses the earliest affected `layer.stage` cutpoint:

```text
layer_XX.data_acquisition
layer_XX.feature_generation
layer_XX.model_generation
layer_XX.model_evaluation
layer_XX.replay_execution
layer_XX.post_replay_attribution
layer_XX.fold_settlement
layer_XX.promotion_review
layer_XX.maintenance
layer_XX.read_model_refresh
```

The planner must compute the downstream closure from that cutpoint and produce both `delete_set` and `protected_set`. The delete set may include generated SQL rows, features, model outputs, model artifacts, replay outputs, attribution outputs, evaluation evidence, promotion-review evidence, read models, runtime state, and workflow completion state. Completed state after the cutpoint must be invalidated or removed, otherwise the scheduler may incorrectly skip the rerun.

Source data is protected by default. It enters `delete_set` only when the cutpoint is `data_acquisition` and the task's required source data changed, the acquisition contract changed, the provider/source parameters changed, or the existing source partition is confirmed wrong, incomplete, duplicated, contaminated, or scoped to an obsolete experiment. When the cutpoint is `feature_generation` or later, source data remains in `protected_set` even if all downstream artifacts are rebuilt.

Deletion scope must be the smallest affected scope: provider/source, target symbol, fold or month window, timeframe, artifact family, and contract/schema. A rerun plan must not use broad "delete everything after this layer" language without concrete refs.

Execution order is downstream deletion/invalidation first, then scheduler reentry from the cutpoint through the current model-group lifecycle. Only one scheduler daemon may own a rerun scope at a time.

## Review and Promotion Contracts

- `manager_dataset_evidence` summarizes snapshot/split/label/eval/control-plane coverage.
- `model_promotion_review_request` asks for promotion review.
- `agent_model_promotion_decision` is advisory evidence only. Offline promotion readiness belongs to `trading-evaluation`; runtime active selection belongs to `trading-execution`.
- `agent_storage_lifecycle_decision` is required for storage lifecycle mutation.
- Agent decisions must cite a fixed workspace skill:
  `promotion-evaluation-review`, `runtime-model-lifecycle-review`, `target-context-review`, `server-error-diagnosis`, `storage-lifecycle-review`, `failure-register-review`, or `event-strategy-promotion-review`.
- Any agent comparison between models must use anonymous model labels. The agent must not know which label is new, old, active, incumbent, champion, challenger, or latest.

## Status Semantics

Use concise lifecycle values such as:

```text
requested | running | succeeded | failed | blocked | cancelled | ready | partial | superseded | expired | deleted
```

A status alone is not enough. Readiness requires evidence refs and a declared consumer scope.

## Boundary

A contract can authorize downstream consumption. It cannot by itself perform provider calls, storage mutation, broker/account mutation, or production activation.
