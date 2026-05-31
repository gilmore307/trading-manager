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

## Workflow Stage Semantics

Historical workflow stages must keep source data, derived features, and model-dependent state separate.

- `data_acquisition` downloads or snapshots source evidence from an external or already-reviewed source surface. It may normalize storage paths, coverage receipts, and point-in-time source refs, but it must not derive model-informed values.
- `feature_generation` derives deterministic data features only from the acquired/source data for the same stage scope. It must be reproducible without reading another model's output, score, decision, or hidden runtime state.
- If a derived table requires any upstream model output, it is not a `feature_generation` output for that source stage. It needs a separate model/input table, an explicit model-generation stage, or a newly named intermediate task with its own contract and blockers.
- Model outputs, replay state, promotion review evidence, and maintenance surfaces must not be stored under source/feature contracts just because they are convenient downstream inputs.

For example, `trading_data.m01_market_regime_feature_generation` is a valid feature surface when it is deterministically derived from acquired market bars. A target/event table that requires TargetStateVectorModel output, EventFailureRiskModel output, or replay portfolio state is not a feature surface under this definition.

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
