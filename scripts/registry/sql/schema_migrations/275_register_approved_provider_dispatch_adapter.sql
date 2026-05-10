-- Register approved provider-dispatch adapter for historical acquisition.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_MMPD001',
    'artifact_type',
    'MANAGER_PROVIDER_DISPATCH_SUMMARY_V1',
    'text',
    'manager_provider_dispatch_summary_v1',
    'trading-manager/src/trading_manager_tasks/provider_dispatch.py',
    'trading-manager;live_call_approval_v1;layer_01_market_regime;01_feed_alpaca_bars',
    'sync_artifact',
    'Manager-side summary for approval-gated historical provider dispatch. Records request count, approval id, validation count, dispatch count, provider-call count, and per-request commands/receipt paths.'
  ),
  (
    'scr_MMPD001',
    'script',
    'MANAGER_APPROVED_PROVIDER_ACQUISITION_DISPATCH',
    'text',
    'PYTHONPATH=src python3 scripts/tasks/dispatch_approved_provider_acquisition.py',
    'trading-manager/scripts/tasks/dispatch_approved_provider_acquisition.py',
    'trading-manager;live_call_approval_v1;layer_01_market_regime;01_feed_alpaca_bars;manager_model_training_workflow_state_v1',
    'sync_artifact',
    'Validates live_call_approval_v1 for Layer 1 historical Alpaca bars acquisition and only runs provider commands when --execute-approved-provider-calls is explicitly supplied.'
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
