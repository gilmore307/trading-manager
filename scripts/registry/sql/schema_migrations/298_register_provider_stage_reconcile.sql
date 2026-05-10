-- Register safe provider-stage receipt/control-plane/coverage reconciliation.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_RECON001',
    'term',
    'MANAGER_PROVIDER_STAGE_RECONCILE',
    'text',
    'manager_provider_stage_reconcile_v1',
    'trading-manager/docs/95_task_system.md',
    'manager_request_v1;component_completion_receipt_v1;run_manifest_v1;artifact_ref_v1;ready_signal_v1;manager_stage_coverage_v1;manager_model_training_workflow_state_v1',
    'sync_artifact',
    'Safe manager-owned post-dispatch reconciliation contract: discovers existing provider completion receipts, normalizes manager control-plane rows, refreshes stage coverage, and optionally advances workflow state without provider calls.'
  ),
  (
    'scr_RECON001',
    'script',
    'MANAGER_RECONCILE_PROVIDER_STAGE',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/reconcile_provider_stage.py',
    '/root/projects/trading-manager/scripts/tasks/reconcile_provider_stage.py',
    'manager_provider_stage_reconcile_v1;manager_stage_coverage_v1;provider_dispatch;failure_register;workflow_state',
    'sync_artifact',
    'Callable manager entrypoint for offline reconciliation after an approved provider batch. It records existing receipts, writes coverage reports, and can refresh workflow state; it never dispatches providers or performs broker/model/storage lifecycle mutations.'
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
