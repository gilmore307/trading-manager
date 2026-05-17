# Schemas

This directory owns machine-verifiable manager control-plane contract schemas.

The schemas are the cross-repository contract authority for concise control-plane rows. Python validators may normalize convenience inputs, but persisted/requested rows must validate here before they are treated as durable evidence or readiness state.

Current first slice:

- `manager_request.schema.json`
- `input_binding.schema.json`
- `run_manifest.schema.json`
- `artifact_ref.schema.json`
- `ready_signal.schema.json`
- `scheduler_lock.schema.json`

Large component payloads remain by reference; these schemas validate ids, status values, refs, clocks, and readiness facts only.
