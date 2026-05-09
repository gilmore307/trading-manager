-- Register unified manager task-system request/receipt handling.

UPDATE trading_registry
SET payload = 'trading_manager.manager_request;trading_manager.input_binding;trading_manager.run_manifest;trading_manager.run_step;trading_manager.artifact_ref;trading_manager.ready_signal',
    path = 'trading-manager/docs/95_task_system.md',
    applies_to = 'trading-manager;control_plane;task_system;component_requests;component_completion_receipts',
    note = 'Minimal manager task-system tables. Requests are centralized in manager_request; component completion receipts are normalized into run_manifest, artifact_ref, and ready_signal rows without embedding component payload bodies.',
    updated_at = NOW()
WHERE key = 'MANAGER_CONTRACT_SQL_TABLES';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_MTS001',
    'config',
    'MANAGER_TASK_SYSTEM_POLICY',
    'text',
    'manager_issues_requests;components_emit_completion_receipts;manager_records_run_artifact_ready_facts;payloads_by_reference;no_component_private_queue_schema_in_manager',
    'trading-manager/docs/95_task_system.md',
    'task_system;manager_request_v1;run_manifest_v1;artifact_ref_v1;ready_signal_v1;all_components',
    'sync_artifact',
    'Unified control-plane policy for all component task requests and completion receipts.'
  ),
  (
    'cfg_MTS002',
    'config',
    'COMPONENT_COMPLETION_RECEIPT_NORMALIZED_ROWS',
    'text',
    'run_manifest_v1;artifact_ref_v1;ready_signal_v1',
    'trading-manager/docs/95_task_system.md',
    'component_completion_receipt_v1;task_system;control_plane',
    'sync_artifact',
    'A component completion receipt payload is summarized by manager as run, artifact-reference, and ready-signal rows. The receipt JSON remains storage/component-owned payload.'
  ),
  (
    'art_MTS001',
    'artifact_type',
    'COMPONENT_COMPLETION_RECEIPT_ARTIFACT',
    'text',
    'component_completion_receipt',
    'trading-manager/docs/95_task_system.md',
    'artifact_ref_v1;component_completion_receipt_v1;task_system',
    'registry_only',
    'Artifact type for a component completion receipt payload referenced by manager artifact_ref rows.'
  ),
  (
    'mft_MTS001',
    'manifest_type',
    'COMPONENT_COMPLETION_RECEIPT_V1',
    'text',
    'component_completion_receipt_v1',
    'trading-manager/docs/95_task_system.md',
    'component_completion_receipt;task_system;all_components',
    'registry_only',
    'Generic manifest/schema reference for component completion receipt payloads normalized into manager control-plane rows.'
  ),
  (
    'rst_MTS001',
    'ready_signal_type',
    'COMPONENT_TASK_READY_SIGNAL',
    'text',
    'component_task_ready',
    'trading-manager/docs/95_task_system.md',
    'ready_signal_v1;task_system;all_components',
    'registry_only',
    'Generic ready signal emitted by manager after normalizing a component completion receipt.'
  ),
  (
    'scr_MTS001',
    'script',
    'MANAGER_REQUEST_SUBMIT',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/submit_manager_requests.py',
    '/root/projects/trading-manager/scripts/tasks/submit_manager_requests.py',
    'task_system;manager_request_v1;control_plane',
    'sync_artifact',
    'Validate or persist manager_request_v1 rows for component tasks.'
  ),
  (
    'scr_MTS002',
    'script',
    'MANAGER_COMPLETION_RECEIPT_RECORD',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/record_completion_receipt.py',
    '/root/projects/trading-manager/scripts/tasks/record_completion_receipt.py',
    'task_system;component_completion_receipt_v1;run_manifest_v1;artifact_ref_v1;ready_signal_v1',
    'sync_artifact',
    'Normalize or persist a component completion receipt as manager run/artifact/ready rows.'
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
