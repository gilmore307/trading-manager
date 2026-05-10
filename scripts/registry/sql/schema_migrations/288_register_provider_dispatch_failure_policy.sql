-- Register provider dispatch per-request failure continuation policy.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_MGRPDISP001',
    'config',
    'MANAGER_PROVIDER_DISPATCH_FAILURE_POLICY',
    'text',
    'approval_gate_required;continue_on_error_allowed_for_per_request_failures;failed_component_receipts_are_ingested;batch_failure_does_not_unlock_stage;broker_and_model_activation_still_forbidden',
    'trading-manager/docs/95_task_system.md',
    'manager_provider_dispatch_summary_v1;live_call_approval_v1;component_completion_receipt_v1;manager_stage_coverage_v1',
    'sync_artifact',
    'After live_call_approval_v1 validation, manager may continue an approved provider batch after individual request failures so failed component receipts can be persisted and reviewed. This does not expand approval scope or unlock downstream workflow stages.'
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
