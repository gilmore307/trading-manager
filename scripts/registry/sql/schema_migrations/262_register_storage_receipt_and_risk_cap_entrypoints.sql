-- Register storage-owned receipt payload helper and execution risk-cap validation entrypoint.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'mft_MTS002',
    'manifest_type',
    'COMPONENT_COMPLETION_RECEIPT_PAYLOAD_V1',
    'text',
    'component_completion_receipt_payload_v1',
    'trading-storage/src/trading_storage/artifact_store.py',
    'component_completion_receipt;trading-storage;artifact_ref_v1;task_system',
    'sync_artifact',
    'Storage-owned JSON wrapper for bulky component completion receipt payloads. Manager SQL stores concise artifact refs and normalized rows, not receipt bodies.'
  ),
  (
    'scr_MTS007',
    'script',
    'STORAGE_COMPLETION_RECEIPT_PAYLOAD_STORE',
    'command',
    'PYTHONPATH=src python3 scripts/artifacts/store_completion_receipt_payload.py',
    '/root/projects/trading-storage/scripts/artifacts/store_completion_receipt_payload.py',
    'component_completion_receipt_payload_v1;artifact_ref_v1;trading-storage;task_system',
    'sync_artifact',
    'Store component completion receipt JSON as a storage-owned payload artifact and emit artifact_ref_v1 metadata.'
  ),
  (
    'scr_TRC001',
    'script',
    'TRADE_RISK_CAP_VALIDATE',
    'command',
    'PYTHONPATH=src python3 scripts/execution/validate_trade_risk_cap.py',
    '/root/projects/trading-execution/scripts/execution/validate_trade_risk_cap.py',
    'trade_risk_cap;decision_record;trading-execution;order_construction;execution_safety',
    'sync_artifact',
    'Validate a unified decision record trade_risk_cap before order construction. Missing or invalid caps exit non-zero and require reject_order.'
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
