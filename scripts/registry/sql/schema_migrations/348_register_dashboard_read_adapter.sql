-- Register the dashboard-side storage-hosted read-model adapter.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_DASHRM004',
    'script',
    'DASHBOARD_READ_MODEL_LATEST_READ',
    'command',
    'PYTHONPATH=src python3 scripts/read_models/read_latest_dashboard_read_model.py',
    '/root/projects/trading-dashboard/scripts/read_models/read_latest_dashboard_read_model.py',
    'dashboard_read_model;trading-dashboard;read_adapter;storage/latest_json;read_only_presentation',
    'sync_artifact',
    'Read one accepted storage-hosted dashboard read-model latest.json file and print a UI-ready JSON view. This adapter is read-only and performs no provider calls, manager dispatch, model activation, broker execution, account mutation, or storage writes.'
  ),
  (
    'cfg_DASHRM006',
    'config',
    'DASHBOARD_READ_MODEL_ADAPTER_MODULE',
    'text',
    'trading_dashboard.read_models',
    '/root/projects/trading-dashboard/src/trading_dashboard/read_models.py',
    'dashboard_read_model;trading-dashboard;read_adapter;storage_hosted_summary;ui_ready_view',
    'sync_artifact',
    'Dashboard-side read adapter module for accepted storage-hosted dashboard read-model latest snapshots. It projects common-envelope summaries into UI-ready dictionaries without querying raw component internals.'
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
