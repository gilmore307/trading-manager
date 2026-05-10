-- Register agent-review-required failure proposals from provider-stage reconciliation.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_RECON002',
    'term',
    'MANAGER_STAGE_FAILURE_REGISTER_PROPOSAL',
    'text',
    'manager_failure_register_v1 rows with failure_status=agent_review_required generated from failed provider receipts',
    'trading-manager/docs/95_task_system.md',
    'manager_provider_stage_reconcile_v1;manager_failure_register_v1;component_completion_receipt_v1;agent_failure_review',
    'sync_artifact',
    'Provider-stage reconciliation may propose or persist observed failures as agent_review_required failure-register rows. These rows preserve failed facts but do not accept, skip, correct, or retry failures until reviewed.'
  )
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();
