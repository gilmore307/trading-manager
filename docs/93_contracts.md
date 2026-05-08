# Contracts

## Purpose

`trading-manager` owns the trading-wide control-plane contracts that let component repositories coordinate without sharing implementation details.

A manager contract must answer one of these questions:

- What component, input, run, artifact, signal, evaluation, review, or activation is being referenced?
- Who produced it, when was it valid, and what evidence proves it?
- Which downstream boundary may consume it?
- What is intentionally outside this contract?

Contracts here are generic platform contracts. They must work across data, model, storage, execution, and dashboard workflows without embedding one component's private schema.

## First-Principles Rules

1. **References over payload duplication.** Manager contracts reference artifacts, datasets, vectors, reports, and outputs; they do not copy full component-owned payloads.
2. **Point-in-time evidence.** Inputs, outputs, evaluations, and approvals must carry enough timing and version evidence to prevent accidental future leakage.
3. **Component neutrality.** A contract may name a component role, but it must not encode model-specific score families, provider API schemas, broker order schemas, or dashboard view schemas.
4. **One lifecycle, many components.** Feed, source, feature, model, evaluation, promotion, execution handoff, and dashboard handoff should reuse the same request/run/artifact/signal skeleton where possible.
5. **Explicit readiness.** Downstream consumers must not infer readiness from file existence, partial logs, or human narrative. They consume ready signals or reviewed decisions.
6. **Review before activation.** Promotion candidates and activation records are separate. Evaluation evidence does not imply activation.
7. **UTC in contracts.** Human planning may use US Eastern time, but contract timestamps use UTC ISO-8601 strings.
8. **No secrets.** Contracts may reference secret aliases or config ids, but must never contain credential material.

## Persistence Policy

Contract persistence follows one rule:

```text
SQL stores durable control-plane facts and audit state.
Storage stores bulky payloads, transient evidence, and retention-managed files.
Temp scratch stores run-local material that never becomes a contract artifact.
```

Do not decide table shape by asking whether a contract name exists. Decide by asking whether the system must later query, audit, resume, retry, review, supersede, or prove that fact.

### SQL Durable Control Plane

Use SQL tables for facts that must survive payload cleanup:

- manager requests;
- run manifests;
- run steps when step-level evidence matters;
- input bindings;
- artifact reference metadata;
- ready signals;
- dataset snapshot metadata;
- evaluation runs;
- metric results;
- promotion candidates;
- review decisions;
- activation records;
- downstream handoff metadata.

SQL rows may point at storage payloads, but they must not store large payloads, raw provider bodies, model vector bodies, logs, or secret material.

### Storage Retention-Managed Payloads

Use storage for payloads that may be large, component-owned, or retention-managed:

- raw logs;
- stdout and stderr captures;
- intermediate JSON, CSV, parquet, or bundle files;
- large model output payloads;
- diagnostics reports;
- source evidence bundles;
- temporary evaluation reports;
- replay bundles;
- scratch snapshots that were promoted to evidence.

If a storage payload participates in a formal request, run, evaluation, review, activation, or handoff, SQL must keep the durable reference metadata: artifact id, URI, hash or fingerprint, producer run, schema reference, retention policy, and current lifecycle state such as active, superseded, archived, deleted, or expired.

### Pure Temp Scratch

Use pure temp storage only for material that never becomes evidence:

- provider probes that are not accepted as source evidence;
- retry-local partial files;
- local debug dumps;
- component-private scratch files;
- failed fragments that are not needed for later review.

Pure temp scratch should not receive contract ids. It may be deleted when the run ends or by routine cleanup.

### Practical Table Rule

Not every contract becomes one SQL table. Some contracts are embedded references, registry-backed values, or JSON substructures inside a durable table. A contract should become a first-class SQL table when it has its own lifecycle, query surface, relationship fan-out, retention state, or audit obligation.

The MVP implementation starts with SQL tables for request, input binding, run, step, artifact reference, and ready-signal state. Component identity is initially registry-backed fields on those tables instead of a separate component catalog table. Add a component catalog only when real query or lifecycle needs require it.

## Contract Inventory

### Core MVP Contracts

These are the first contracts to design and implement because every later workflow depends on them.

| Contract | Owns | Does Not Own |
|---|---|---|
| `component_ref_v1` | Stable reference to a runnable or producing component. | Runtime implementation, source code, package installation. |
| `manager_request_v1` | Manager-issued request for work. | Component-internal task queue semantics. |
| `input_binding_v1` | Point-in-time binding between a run and its inputs. | Full input data payloads. |
| `run_manifest_v1` | Evidence of what actually ran. | Large logs, full output datasets, or model internals. |
| `run_step_v1` | Optional ordered run sub-steps. | Fine-grained component-local tracing. |
| `artifact_ref_v1` | Durable reference to a produced artifact. | Artifact bytes or storage engine internals. |
| `ready_signal_v1` | Explicit statement that a producer output is consumable. | Approval to promote or activate. |

### Evaluation And Promotion Contracts

These layer on top of the MVP contracts once runs and artifacts can be referenced reliably.

| Contract | Owns | Does Not Own |
|---|---|---|
| `dataset_snapshot_v1` | Evaluation/training/replay dataset identity and point-in-time boundary. | Raw market data storage. |
| `model_output_envelope_v1` | Generic wrapper around model outputs. | Model-specific vector field definitions. |
| `evaluation_run_v1` | Evaluation setup and evidence links. | Model training implementation. |
| `metric_result_v1` | Individual metric result with threshold/evidence context. | Metric implementation code. |
| `promotion_candidate_v1` | Candidate package for review. | Production activation. |
| `review_decision_v1` | Human/agent review outcome. | Automatic mutation of runtime configs. |
| `activation_record_v1` | Approved activation/change record with rollback reference. | Broker or order execution. |

### Downstream Handoff Contracts

These prevent manager/model outputs from pretending to be execution, storage, or dashboard implementation.

| Contract | Owns | Does Not Own |
|---|---|---|
| `downstream_handoff_v1` | Boundary-crossing handoff to storage, execution, dashboard, or audit. | The downstream component's internal lifecycle. |
| `execution_intent_ref_v1` | Optional reference to an execution-owned intent accepted for processing. | Broker orders, fills, positions, or account mutation. |

`execution_intent_ref_v1` is intentionally a reference contract, not an order contract. Broker order lifecycle belongs to `trading-execution`.

## Core Contract Skeletons

### `component_ref_v1`

Use this whenever a contract needs to identify a producer, consumer, runnable script, model layer, source, feature generator, or review helper.

Required fields:

| Field | Meaning |
|---|---|
| `contract_type` | Literal `component_ref_v1`. |
| `component_id` | Stable registry id or reviewed component id. |
| `component_kind` | Generic role such as `data_feed`, `data_source`, `data_feature`, `model`, `review_helper`, `execution_service`, `dashboard_surface`. |
| `repo_id` | Stable repository id. |
| `version_ref` | Git commit, release tag, or immutable build id. |
| `entrypoint_ref` | Script/helper/command reference when runnable. |

Optional fields:

- `layer_id`
- `owner_repo_path`
- `registry_ref`
- `notes`

### `manager_request_v1`

A manager request is the control-plane instruction to do work. It is not proof that work happened.

Required fields:

| Field | Meaning |
|---|---|
| `contract_type` | Literal `manager_request_v1`. |
| `request_id` | Stable unique request id. |
| `request_kind` | Generic request class: `produce_data`, `run_model`, `evaluate_model`, `review_promotion`, `handoff_downstream`, etc. |
| `created_at_utc` | UTC ISO-8601 creation time. |
| `requested_by` | Human, agent, scheduler, or parent request reference. |
| `target_component` | `component_ref_v1`. |
| `input_bindings` | One or more `input_binding_v1` records or refs. |
| `expected_outputs` | Output type names or artifact expectations. |
| `policy_refs` | Guardrail, retry, live-call, promotion, or safety policy refs. |

Optional fields:

- `priority`
- `deadline_at_utc`
- `idempotency_key`
- `parent_request_id`
- `parameter_ref`
- `dry_run`
- `manual_override_ref`

### `input_binding_v1`

Input binding makes the run's inputs explicit and reproducible.

Required fields:

| Field | Meaning |
|---|---|
| `contract_type` | Literal `input_binding_v1`. |
| `binding_id` | Stable unique binding id. |
| `input_role` | Role such as `feature_table`, `source_artifact`, `model_output`, `dataset_snapshot`, `config`, `policy`, `secret_alias`. |
| `input_ref` | Artifact, table, registry, dataset, or config reference. |
| `available_at_utc` | Earliest valid availability time for this input. |
| `as_of_utc` | Point-in-time cutoff for leakage control. |
| `version_ref` | Hash, commit, migration id, snapshot id, or storage version. |

Optional fields:

- `entity_scope`
- `time_window`
- `schema_ref`
- `quality_ref`
- `lineage_ref`

### `run_manifest_v1`

A run manifest records what actually happened.

Required fields:

| Field | Meaning |
|---|---|
| `contract_type` | Literal `run_manifest_v1`. |
| `run_id` | Stable unique run id. |
| `request_id` | Source manager request. |
| `component` | `component_ref_v1` for the component that ran. |
| `status` | Lifecycle status from the registry. |
| `started_at_utc` | UTC ISO-8601 start time. |
| `ended_at_utc` | UTC ISO-8601 end time or null while running. |
| `input_bindings` | Bound inputs used by the run. |
| `output_artifacts` | Produced `artifact_ref_v1` refs. |
| `run_steps` | Optional `run_step_v1` refs. |

Optional fields:

- `environment_ref`
- `parameter_ref`
- `stdout_ref`
- `stderr_ref`
- `error_summary`
- `retry_of_run_id`
- `checkpoint_ref`

### `run_step_v1`

Run steps are optional. Use them when a run has meaningful phases that downstream review may need.

Required fields:

| Field | Meaning |
|---|---|
| `contract_type` | Literal `run_step_v1`. |
| `step_id` | Stable unique step id. |
| `run_id` | Owning run. |
| `step_name` | Human-readable phase name. |
| `step_order` | Integer ordering within the run. |
| `status` | Lifecycle status. |
| `started_at_utc` | UTC ISO-8601 start time. |
| `ended_at_utc` | UTC ISO-8601 end time or null while running. |

Optional fields:

- `input_refs`
- `output_refs`
- `metric_refs`
- `error_summary`

### `artifact_ref_v1`

An artifact ref describes a durable output without storing the artifact itself.

Required fields:

| Field | Meaning |
|---|---|
| `contract_type` | Literal `artifact_ref_v1`. |
| `artifact_id` | Stable unique artifact id. |
| `artifact_kind` | Registered artifact type. |
| `producer_run_id` | Run that produced it. |
| `uri` | Storage locator or table locator. |
| `content_hash` | Hash/fingerprint when applicable. |
| `created_at_utc` | UTC ISO-8601 creation time. |
| `schema_ref` | Schema, manifest, or contract reference. |

Optional fields:

- `byte_size`
- `row_count`
- `partition_ref`
- `retention_policy_ref`
- `compression`
- `media_type`
- `lineage_ref`

### `ready_signal_v1`

A ready signal is the producer's explicit statement that a downstream boundary may consume an output.

Required fields:

| Field | Meaning |
|---|---|
| `contract_type` | Literal `ready_signal_v1`. |
| `ready_signal_id` | Stable unique signal id. |
| `signal_kind` | Registered ready-signal type. |
| `producer_component` | `component_ref_v1`. |
| `producer_run_id` | Producing run. |
| `artifact_refs` | One or more consumable artifacts. |
| `status` | Ready, blocked, partial, superseded, or failed status. |
| `created_at_utc` | UTC ISO-8601 signal time. |

Optional fields:

- `consumer_hint`
- `blocking_reason`
- `supersedes_ready_signal_id`
- `quality_gate_refs`
- `review_required`

## Evaluation And Promotion Skeletons

### `dataset_snapshot_v1`

Required fields:

- `contract_type`
- `dataset_snapshot_id`
- `dataset_kind`
- `input_bindings`
- `entity_universe_ref`
- `time_window`
- `as_of_utc`
- `row_count`
- `content_hash`
- `schema_ref`

This contract owns dataset identity and leakage boundaries. It does not own storage internals or raw data payloads.

### `model_output_envelope_v1`

Required fields:

- `contract_type`
- `model_output_id`
- `model_component`
- `run_id`
- `layer_id`
- `entity_ref`
- `horizon_ref`
- `available_at_utc`
- `as_of_utc`
- `payload_ref`
- `diagnostics_ref`

The payload may contain `market_context_state`, `sector_context_state`, `target_context_state`, `event_context_vector`, `alpha_confidence_vector`, `position_projection_vector`, `underlying_action_vector`, or `expression_vector`, but the envelope does not define those vector fields.

### `evaluation_run_v1`

Required fields:

- `contract_type`
- `evaluation_run_id`
- `evaluated_component`
- `dataset_snapshot_ref`
- `split_spec_ref`
- `label_spec_ref`
- `baseline_refs`
- `metric_result_refs`
- `run_manifest_ref`

### `metric_result_v1`

Required fields:

- `contract_type`
- `metric_result_id`
- `metric_name`
- `metric_scope`
- `value`
- `threshold_ref`
- `pass_fail_status`
- `split_ref`
- `horizon_ref`
- `evidence_ref`

### `promotion_candidate_v1`

Required fields:

- `contract_type`
- `promotion_candidate_id`
- `component_ref`
- `candidate_config_ref`
- `evaluation_run_refs`
- `metric_result_refs`
- `baseline_comparison_refs`
- `known_blockers`
- `created_at_utc`

A promotion candidate is reviewable evidence. It is not activation.

### `review_decision_v1`

Required fields:

- `contract_type`
- `review_decision_id`
- `review_target_ref`
- `reviewer_ref`
- `decision_status`
- `decision_reason`
- `conditions`
- `created_at_utc`

Allowed statuses should remain registry vocabulary: approve, defer, reject, revoke, or supersede.

### `activation_record_v1`

Required fields:

- `contract_type`
- `activation_record_id`
- `activated_component`
- `approved_review_decision_ref`
- `activated_config_ref`
- `replaced_config_ref`
- `rollback_ref`
- `activated_at_utc`
- `activated_by`

Activation records are only valid after an approving review decision. They do not execute broker or exchange actions.

## Downstream Handoff Skeletons

### `downstream_handoff_v1`

Required fields:

- `contract_type`
- `handoff_id`
- `handoff_kind`
- `source_component`
- `target_component_role`
- `source_run_id`
- `artifact_refs`
- `ready_signal_ref`
- `handoff_status`
- `created_at_utc`

Use this contract when manager passes durable work to storage, execution, dashboard, or audit boundaries.

### `execution_intent_ref_v1`

Required fields:

- `contract_type`
- `execution_intent_ref_id`
- `source_handoff_id`
- `execution_owner_component`
- `intent_ref`
- `accepted_at_utc`
- `status`

This is a reference to execution-owned intent handling. It must not include broker order payloads, order ids, fills, positions, or account mutation fields.

## Lifecycle Relationship

```text
manager_request_v1
  -> input_binding_v1[]
  -> run_manifest_v1
       -> run_step_v1[]
       -> artifact_ref_v1[]
       -> ready_signal_v1
            -> downstream_handoff_v1

For model evaluation/promotion:

run_manifest_v1
  -> dataset_snapshot_v1
  -> model_output_envelope_v1[]
  -> evaluation_run_v1
       -> metric_result_v1[]
       -> promotion_candidate_v1
            -> review_decision_v1
                 -> activation_record_v1
```

## Cross-Repository Ownership

| Repo | Relationship To These Contracts |
|---|---|
| `trading-manager` | Defines contract vocabulary, review rules, registry names, lifecycle policy, and control-plane validation. |
| `trading-data` | Produces feed/source/feature outputs and emits run/artifact/ready evidence through these contracts. |
| `trading-model` | Produces model outputs, evaluation evidence, metric results, and promotion candidates through these contracts. |
| `trading-storage` | Owns durable physical persistence, retention, rehydrate, backup, and restore expectations for referenced artifacts. |
| `trading-execution` | Owns execution intents, broker/order lifecycle, positions, reconciliation, and safety-sensitive mutations. |
| `trading-dashboard` | Consumes reviewed outputs and handoffs for display; owns UI schemas and rendering. |

## Explicit Non-Contracts

The following must not be introduced as manager contracts unless a separate architecture decision changes the boundary:

- provider raw API response schemas;
- model-specific score-family field catalogs;
- broker order payloads;
- fills, positions, and account balance mutation records;
- dashboard widget/view schemas;
- filesystem directory implementation details;
- secrets, tokens, private keys, or credential payloads;
- component-local debug logs except as `artifact_ref_v1` references.

## MVP Implementation Status

The first implementation slice is intentionally small:

| Contract | SQL table |
|---|---|
| `manager_request_v1` | `trading_manager.manager_request` |
| `input_binding_v1` | `trading_manager.input_binding` |
| `run_manifest_v1` | `trading_manager.run_manifest` |
| `run_step_v1` | `trading_manager.run_step` |
| `artifact_ref_v1` | `trading_manager.artifact_ref` |
| `ready_signal_v1` | `trading_manager.ready_signal` |

`component_ref_v1` is not a table yet. It is represented by registry-backed component/repo/version/entrypoint fields on the durable tables.

Next implementation order:

1. Add lightweight validation/helper code after the first real consumer appears.
2. Add evaluation/promotion SQL tables once run/artifact/ready persistence is exercised.
3. Add downstream handoff tables before connecting Layer 8 outputs to execution-owned workflows.
4. Add a component catalog only if query or lifecycle pressure proves it is needed.

## Acceptance Checklist

A manager contract design or implementation change is acceptable only when:

- the contract has a clear owner and non-owner boundary;
- required fields are minimal but sufficient for reproducibility and downstream validation;
- timestamps use UTC ISO-8601 semantics;
- point-in-time and version evidence are present where leakage or reproducibility matters;
- generated artifacts are referenced, not embedded;
- component-specific schemas remain in component repositories;
- new shared field/status/type names are routed through the registry before cross-repository use;
- no secrets or generated runtime artifacts are stored in `trading-manager`;
- tests, registry dry-run, and docs spine updates are complete when implementation begins.
