# Tasks

This file is the current task ledger for `trading-manager`. It should stay short. Detailed history belongs in Git and immutable registry migrations, not in active task text.

## Current Direction

The resident historical scheduler is the normal path for no-broker historical modeling. Manual task scripts are inspection, repair, smoke-test, or emergency tools unless a task explicitly says otherwise.

## Active Tasks

1. **Documentation reset**
   - Reorganize manager Markdown from first principles.
   - Remove stale route-change prose from active docs.
   - Preserve fixed entry files and registry references.

2. **Historical scheduler supervision**
   - Keep the service in the historical/no-broker boundary.
   - Confirm provider/model/storage/broker gates remain explicit.
   - Use status scripts for evidence rather than chat memory.

3. **Layer 1/2 foundation catch-up**
   - Continue targetless Layer 1 market/cross-asset and Layer 2 sector/industry progression before ordinary Layer 3+ target work.
   - Reuse valid point-in-time provider data/features/coverage evidence.
   - Rebuild model/evaluation/promotion artifacts when their substrate changed.

4. **Layer 9 event-risk lane**
   - Keep event-source research inside the same historical-modeling service boundary.
   - Realtime observation pool admits only reviewed event families.
   - Layer 4 consumes only accepted Layer 9 evidence packets.

## Standing Gates

- Provider calls require the explicit provider-dispatch path and request/coverage controls.
- Model activation requires accepted `agent_model_promotion_decision` evidence.
- Storage lifecycle mutation requires accepted lifecycle policy, protected-set checks, and receipts.
- Broker/order/fill/account mutation belongs only to `trading-execution`.
- `review_required_overlap_unknown` event/activity evidence is review/provenance only; it cannot score or intervene.

## Recently Accepted Scope

- Manager control-plane MVP is accepted: request persistence, payload materialization, handoff validation, receipt normalization, task summary, scheduler state, and dashboard/status payloads.
- Historical scheduler may execute safe offline stages and bounded provider dispatches under explicit gates.
- Layer 9 may prepare residual event-risk evidence and promotion packets without turning into direct alpha or execution.

## No Active Task

- Do not expand broker/realtime execution from this repository.
- Do not add broad event families to realtime monitoring without review.
- Do not register ordinary implementation files as `kind=script` rows.
