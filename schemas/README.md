# Schemas

This directory owns machine-verifiable manager control-plane contract schemas.

The schemas are the cross-repository contract authority for concise control-plane rows. Python validators may normalize convenience inputs, but persisted/requested rows must validate here before they are treated as durable evidence or readiness state. Planner previews may include convenience metadata, but they validate against the separate preview schema and must normalize to `manager_request.schema.json` before SQL persistence.

Current first slice:

- `manager_request.schema.json` — concise persisted `trading_manager.manager_request` row.
- `manager_request_planner_preview.schema.json` — CLI/planner preview row with convenience fields such as month, symbol, model, or candidate refs.
- `input_binding.schema.json`
- `run_manifest.schema.json`
- `artifact_ref.schema.json`
- `ready_signal.schema.json`
- `scheduler_lock.schema.json`
- `model_group_rerun_plan.schema.json` — dry-run-first invalidation and regeneration plan for architecture-driven model group reruns.

Large component payloads remain by reference; these schemas validate ids, status values, refs, clocks, and readiness facts only.
