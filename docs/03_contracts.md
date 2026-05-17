# Contracts

Manager contracts are concise, durable control-plane facts. They let components work independently while preserving auditability and downstream readiness.

## Persistence Policy

| Material | Home | Rule |
|---|---|---|
| Control-plane facts | Manager SQL | Keep ids, statuses, refs, timestamps, component ids, hashes, and readiness facts. |
| Large payloads/artifacts/logs | Storage or runtime paths | Store by reference; do not duplicate blobs into SQL. |
| Temporary scratch | Ignored runtime paths | Never treat as evidence unless promoted by receipt/artifact ref. |
| Secrets | Outside repository | Reference only by alias/registry id. |

## Core Contracts

### `manager_request_v1`

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

### `input_binding_v1`

A durable binding between a request and the input refs it may use.

```text
request_id
input_role
input_ref
schema_ref
available_time or as_of_time
```

### `run_manifest_v1`

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

### `run_step_v1`

Optional step-level detail for long runs.

```text
run_id
step_id
step_name
status
started_time
ended_time
```

### `artifact_ref_v1`

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

### `ready_signal_v1`

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

## Review and Promotion Contracts

- `manager_dataset_evidence` summarizes snapshot/split/label/eval/control-plane coverage.
- `model_promotion_review_request` asks for promotion review.
- `agent_model_promotion_decision` is required for production activation.
- `agent_storage_lifecycle_decision` is required for storage lifecycle mutation.

## Status Semantics

Use concise lifecycle values such as:

```text
requested | running | succeeded | failed | blocked | cancelled | ready | partial | superseded | expired | deleted
```

A status alone is not enough. Readiness requires evidence refs and a declared consumer scope.

## Boundary

A contract can authorize downstream consumption. It cannot by itself perform provider calls, storage mutation, broker/account mutation, or production activation.
