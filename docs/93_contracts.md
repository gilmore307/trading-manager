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
| `component_ref` | Stable reference to a runnable or producing component. | Runtime implementation, source code, package installation. |
| `manager_request` | Manager-issued request for work. | Component-internal task queue semantics. |
| `input_binding` | Point-in-time binding between a run and its inputs. | Full input data payloads. |
| `run_manifest` | Evidence of what actually ran. | Large logs, full output datasets, or model internals. |
| `run_step` | Optional ordered run sub-steps. | Fine-grained component-local tracing. |
| `artifact_ref` | Durable reference to a produced artifact. | Artifact bytes or storage engine internals. |
| `ready_signal` | Explicit statement that a producer output is consumable. | Approval to promote or activate. |

### Evaluation And Promotion Contracts

These layer on top of the MVP contracts once runs and artifacts can be referenced reliably.

| Contract | Owns | Does Not Own |
|---|---|---|
| `dataset_snapshot` | Evaluation/training/replay dataset identity and point-in-time boundary. | Raw market data storage. |
| `model_output_envelope` | Generic wrapper around model outputs. | Model-specific vector field definitions. |
| `evaluation_run` | Evaluation setup and evidence links. | Model training implementation. |
| `metric_result` | Individual metric result with threshold/evidence context. | Metric implementation code. |
| `promotion_candidate` | Candidate package for review. | Production activation. |
| `review_decision` | Legacy/advisory review outcome. | Production activation. |
| `activation_record` | Approved activation/change record with rollback reference. | Broker or order execution. |

### Live-Call Approval Contracts

These contracts gate provider/API calls after dry-run planning and before component dispatch.

| Contract | Owns | Does Not Own |
|---|---|---|
| `autonomous_historical_provider_acquisition` | Bounded manager-owned historical provider/data acquisition after payload preparation. | Broker/order/account mutation, model activation, or model promotion approval. |

Historical provider acquisition no longer requires per-batch `autonomous_historical_provider_acquisition`. The active contract is bounded by manager request ids, resource gates, terminal-coverage guards, provider receipts, and reconciliation. Broker execution, order construction, account mutation, model activation, and promotion remain outside this contract.

### Downstream Handoff Contracts

These prevent manager/model outputs from pretending to be execution, storage, or dashboard implementation.

| Contract | Owns | Does Not Own |
|---|---|---|
| `downstream_handoff` | Boundary-crossing handoff to storage, execution, dashboard, or audit. | The downstream component's internal lifecycle. |
| `execution_intent_ref` | Optional reference to an execution-owned intent accepted for processing. | Broker orders, fills, positions, or account mutation. |

`execution_intent_ref` is intentionally a reference contract, not an order contract. Broker order lifecycle belongs to `trading-execution`.

## Core Contract Skeletons

### `component_ref`

Use this whenever a contract needs to identify a producer, consumer, runnable script, model layer, source, feature generator, or review helper.

Required fields:

| Field | Meaning |
|---|---|
| `contract_type` | Literal `component_ref`. |
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

### `manager_request`

A manager request is the control-plane instruction to do work. It is not proof that work happened.

Required fields:

| Field | Meaning |
|---|---|
| `contract_type` | Literal `manager_request`. |
| `request_id` | Stable unique request id. |
| `request_kind` | Generic request class: `produce_data`, `run_model`, `evaluate_model`, `review_promotion`, `handoff_downstream`, etc. |
| `created_at_utc` | UTC ISO-8601 creation time. |
| `requested_by` | Human, agent, scheduler, or parent request reference. |
| `target_component` | `component_ref`. |
| `input_bindings` | One or more `input_binding` records or refs. |
| `expected_outputs` | Output type names or artifact expectations. |
| `policy_refs` | Guardrail, retry, provider-call, promotion, or safety policy refs. |

Optional fields:

- `priority`
- `deadline_at_utc`
- `idempotency_key`
- `parent_request_id`
- `parameter_ref`
- `dry_run`
- `manual_override_ref`

### `input_binding`

Input binding makes the run's inputs explicit and reproducible.

Required fields:

| Field | Meaning |
|---|---|
| `contract_type` | Literal `input_binding`. |
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

### `run_manifest`

A run manifest records what actually happened.

Required fields:

| Field | Meaning |
|---|---|
| `contract_type` | Literal `run_manifest`. |
| `run_id` | Stable unique run id. |
| `request_id` | Source manager request. |
| `component` | `component_ref` for the component that ran. |
| `status` | Lifecycle status from the registry. |
| `started_at_utc` | UTC ISO-8601 start time. |
| `ended_at_utc` | UTC ISO-8601 end time or null while running. |
| `input_bindings` | Bound inputs used by the run. |
| `output_artifacts` | Produced `artifact_ref` refs. |
| `run_steps` | Optional `run_step` refs. |

Optional fields:

- `environment_ref`
- `parameter_ref`
- `stdout_ref`
- `stderr_ref`
- `error_summary`
- `retry_of_run_id`
- `checkpoint_ref`

### `run_step`

Run steps are optional. Use them when a run has meaningful phases that downstream review may need.

Required fields:

| Field | Meaning |
|---|---|
| `contract_type` | Literal `run_step`. |
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

### `artifact_ref`

An artifact ref describes a durable output without storing the artifact itself.

Required fields:

| Field | Meaning |
|---|---|
| `contract_type` | Literal `artifact_ref`. |
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

### `ready_signal`

A ready signal is the producer's explicit statement that a downstream boundary may consume an output.

Required fields:

| Field | Meaning |
|---|---|
| `contract_type` | Literal `ready_signal`. |
| `ready_signal_id` | Stable unique signal id. |
| `signal_kind` | Registered ready-signal type. |
| `producer_component` | `component_ref`. |
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

### `dataset_snapshot`

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

### `model_output_envelope`

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

### `evaluation_run`

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

### `metric_result`

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

### `promotion_candidate`

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

### `agent_model_promotion_decision`

Required fields:

- `contract_type`
- `agent_model_promotion_decision_id`
- `promotion_request_ref`
- `agent_ref`
- `decision_status`
- `decision_reason`
- `evidence_refs`
- `conditions`
- `owner_observed_automation`
- `created_at_utc`

Allowed statuses should remain registry vocabulary: approve, defer, reject, revoke, or supersede. This script-called agent decision is required before production model activation.

### `review_decision`

Required fields:

- `contract_type`
- `review_decision_id`
- `review_target_ref`
- `reviewer_ref`
- `decision_status`
- `decision_reason`
- `conditions`
- `created_at_utc`

Allowed statuses should remain registry vocabulary: approve, defer, reject, revoke, or supersede. This contract is advisory evidence only; it is not sufficient for production activation.

### `target_layer2_context_agent_review_request`

Required fields:

- `contract_type`
- `schema_version`
- `request_id`
- `agent_ref`
- `review_scope`
- `mapping_ref`
- `mapping_path`
- `target_symbols`
- `mapping_rows`
- `required_checks`
- `forbidden_actions`
- `agent_prompt`
- `created_at_utc`

This script-called request asks an agent to review target-to-Layer-2 context and auxiliary proxy mappings. It is evidence-only and must not call providers, activate models, mutate broker/accounts, execute storage lifecycle operations, or edit Layer 1/2 universe files.

### `target_layer2_context_agent_review_decision`

Required fields:

- `contract_type`
- `schema_version`
- `decision_id`
- `request_ref`
- `agent_ref`
- `decision_status`
- `decision_reason`
- `completed_at_utc`

Allowed statuses are `approved`, `deferred`, `rejected`, `queued`, and `agent_call_failed`. An approved review confirms the selected mapping rows are acceptable as target-study metadata; it does not itself change repository files or registry rows.

### `activation_record`

Required fields:

- `contract_type`
- `activation_record_id`
- `activated_component`
- `approved_agent_model_promotion_decision_ref`
- `activated_config_ref`
- `replaced_config_ref`
- `rollback_ref`
- `activated_at_utc`
- `activated_by`

Activation records are only valid after an approving `agent_model_promotion_decision`. They do not execute broker or exchange actions.

## Downstream Handoff Skeletons

### `downstream_handoff`

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

### `execution_intent_ref`

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

All component work uses the same task-system skeleton. Manager issues requests; components return completion receipts; manager records the durable receipt summary as run, artifact, and ready-signal facts.

```text
manager_request
  -> component completion receipt
  -> input_binding[]
  -> run_manifest
       -> run_step[]
       -> artifact_ref[]
       -> ready_signal
            -> downstream_handoff

For model evaluation/promotion:

model_promotion_review manager request
  -> run_manifest
  -> dataset_snapshot
  -> model_output_envelope[]
  -> evaluation_run
       -> metric_result[]
       -> promotion_candidate
            -> agent_model_promotion_decision
                 -> activation_record
```

`model_promotion_review` is the single manager-side entrypoint for every model layer. Layer-specific differences belong in evidence adapters, labels, metrics, baseline ladders, and gate policy refs, not in separate promotion mechanisms.

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
- component-local debug logs except as `artifact_ref` references.

## MVP Implementation Status

The first implementation slice is intentionally small:

| Contract | SQL table |
|---|---|
| `manager_request` | `trading_manager.manager_request` |
| `input_binding` | `trading_manager.input_binding` |
| `run_manifest` | `trading_manager.run_manifest` |
| `run_step` | `trading_manager.run_step` |
| `artifact_ref` | `trading_manager.artifact_ref` |
| `ready_signal` | `trading_manager.ready_signal` |

`component_ref` is not a table yet. It is represented by registry-backed component/repo/version/entrypoint fields on the durable tables.

The first task-system helper slice is also implemented: `scripts/tasks/submit_manager_requests.py` validates/persists manager requests, `scripts/tasks/record_completion_receipt.py` normalizes component completion receipts into `run_manifest`, `artifact_ref`, and `ready_signal` rows, `trading_manager.task_summary` / `scripts/tasks/list_task_summary.py` expose the global priority-ordered task summary, `scripts/tasks/plan_model_promotion_review.py` plans the single manager-side promotion review request kind for all model layers, and `scripts/tasks/dispatch_provider_acquisition.py` plans or executes bounded autonomous provider dispatch.

Current manager closeout stance:

1. Request/receipt/task-summary MVP is implemented and rehearsed.
2. Model-promotion review routing and decision/activation artifact builders are implemented.
3. Owner-observed provider-call agent-review/validation is defined and registered; provider dispatch remains bounded to historical provider acquisition scope.
4. Broker/order/fill/account lifecycle remains outside `trading-manager` and must stay execution-owned.
5. A component catalog or additional SQL tables should be added only when real query or lifecycle pressure proves they are needed.

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
