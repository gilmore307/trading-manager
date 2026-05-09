# Task

## Active Tasks

- None for the historical-data training preparation boundary.

The manager/control-plane MVP is closed for no-broker historical training: planning, request persistence, payload materialization, dry-run handoff validation, receipt normalization, task summary, review-decision artifacts, and live-call approval validation are accepted.

## Historical-Training Todo Status

- Seven bounded `2016-01` dry-run monthly request/receipt paths are closed as `ready` with one artifact each.
- Provider acquisition is intentionally gated: non-dry-run historical data calls require reviewed `live_call_approval_v1` and validation before any component dispatch is considered.
- Model promotion requests can be planned through `model_promotion_review_v1`, but production activation requires an approving `review_decision_v1` and remains out of the current no-broker training scope.

## Not Current Historical-Training Scope

These items are intentionally outside the current no-broker historical-training run and must not be treated as active manager work items:

- live provider dispatch workers without validated `live_call_approval_v1` artifacts;
- broker/order-construction implementation;
- execution-owned order/fill/account lifecycle;
- durable object-store and high-volume SQL partitioning beyond the current storage-owned payload helper and manager SQL summary rows;
- migration of legacy local staging into durable storage contracts before a concrete training consumer requires it.

## Recently Accepted

- Closed the current manager/control-plane phase in `docs/97_manager_control_plane_closeout.md`: request/run/artifact/ready MVP, task summary, monthly backfill planning, request payload materialization, dry-run handoff validation, unified model-promotion route, review decision/activation artifact builders, storage receipt payload reference flow, and live-call approval gate are accepted. No provider dispatch, broker execution, or production activation is enabled by this closeout.
- Added `live_call_approval_v1` and `scripts/tasks/validate_live_call_approval.py` as the explicit data-acquisition-only gate before any non-dry-run provider handoff. The gate requires bounded approved request ids, provider allowlist, max request count, max window days, expiry, and `broker_execution_allowed=false`.
- Closed all seven bounded `2016-01` dry-run monthly request/receipt paths: storage-owned receipt payloads were materialized in `trading-storage`, manager normalized them into SQL run/artifact/ready rows, and `task_summary` now reports each dry-run request as `ready` with `artifact_count=1`; no provider calls, component runs, or production data outputs occurred.
- Registered storage receipt-payload and execution risk-cap validation entrypoints through migration `262_register_storage_receipt_and_risk_cap_entrypoints.sql`.
- Added concrete unified review decision artifacts: `review_decision_v1` and `activation_record_v1` builders/tests, plus script `scripts/tasks/build_review_decision.py`. Activation records require an approving review decision.
- Added component-facing handoff validation: `scripts/tasks/validate_request_handoff.py` loads materialized request payloads, verifies hash-backed input bindings and dry-run policy, and calls only target component `build_context` without dispatching work or calling providers.
- Added request payload materialization: `scripts/tasks/materialize_request_payloads.py` writes component-readable `task_key.json` payloads behind `manager_request.parameter_ref` and can persist request-scoped `input_binding_v1` metadata without provider calls or component dispatch.
- Added deterministic task-system rehearsal entrypoint: `scripts/tasks/rehearse_task_system.py` exercises manager request, component receipt, run manifest, artifact ref, ready signal, and task-summary-like rows without provider calls or SQL writes.
- Added unified model promotion review entrypoint: all model layers now use `model_promotion_review_v1` manager requests through `scripts/tasks/plan_model_promotion_review.py`; model-specific code only produces evidence/adapters.
- Added global task summary: `trading_manager.task_summary` derives every manager request's current status, latest run, latest ready signal, artifact count, priority, and priority rank for ordered dashboards/CLIs.
- Added unified manager task-system request/receipt handling: manager requests are validated/persisted centrally, and component completion receipts normalize into run-manifest, artifact-ref, and ready-signal facts.
- Added monthly historical backfill planning: common start `2016-01`, OKX crypto joins at `2018-01`, and current-only feeds stay out of historical point-in-time backfill until a new route is accepted.
- Implemented and registered the concise MVP manager/control-plane SQL tables: `trading_manager.manager_request`, `trading_manager.input_binding`, `trading_manager.run_manifest`, `trading_manager.run_step`, `trading_manager.artifact_ref`, and `trading_manager.ready_signal`. `component_ref_v1` remains registry-backed fields rather than a separate component catalog table.
- Added first-principles manager contract design in `docs/93_contracts.md`, including core MVP contracts, evaluation/promotion contracts, downstream handoff contracts, ownership boundaries, lifecycle relationships, persistence policy, and implementation order.
- Registered manager/storage V1 handoff contracts and hardening policies: `manager_request_v1`, `run_manifest_v1`, `artifact_ref_v1`, `ready_signal_v1`, live-call guardrails, checkpoint/resume policy, and data-production hardening policy.
- Registered full production-promotion closeout decisions: Layers 1-2 have real database evidence and persisted deferred decisions; Layer 3 now has real production-evaluation substrate but remains deferred by upstream approvals/calibration; Layers 4-8 have persisted blocked eval runs, metrics, candidates, and reviewer-agent deferred decisions for missing production eval substrate; no production activation is approved.
- Registered `trading-data` closeout readiness policies: data-source/model-input design closed, ETF holdings default visibility at next regular US session open after `as_of_date`, and `equity_abnormal_activity_conservative_v1` as conservative/non-production-calibrated until reviewed historical evidence exists.
