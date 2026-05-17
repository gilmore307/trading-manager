# Schemas

This directory owns machine-verifiable manager control-plane contract schemas.

The schemas are the cross-repository contract authority for concise control-plane rows. Python validators may normalize convenience inputs, but persisted/requested rows must validate here before they are treated as durable evidence or readiness state.

Current first slice:

- `manager_request_v1.schema.json`
- `input_binding_v1.schema.json`
- `run_manifest_v1.schema.json`
- `artifact_ref_v1.schema.json`
- `ready_signal_v1.schema.json`
- `scheduler_lock_v1.schema.json`

Large component payloads remain by reference; these schemas validate ids, status values, refs, clocks, and readiness facts only.
