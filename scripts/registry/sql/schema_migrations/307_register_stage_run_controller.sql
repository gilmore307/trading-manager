-- Register conservative single-step stage run controller.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_SRCT001',
    'term',
    'MANAGER_STAGE_RUN_CONTROLLER_RECEIPT',
    'text',
    'manager_stage_run_controller_receipt_v1',
    'trading-manager/docs/95_task_system.md',
    'manager_stage_run_dashboard_v1;manager_live_call_approval_packet_v1;pending_only_live_call_packet_planning_v1',
    'sync_artifact',
    'Receipt for one conservative manager stage-run controller step. The controller may create the next pending-only packet and refresh the dashboard, but stops at approval review, provider execution, failure review, model activation, broker execution, and storage lifecycle gates.'
  ),
  (
    'scr_SRCT001',
    'script',
    'MANAGER_RUN_STAGE_CONTROLLER',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/run_stage_controller.py',
    '/root/projects/trading-manager/scripts/tasks/run_stage_controller.py',
    'manager_stage_run_controller_receipt_v1;manager_stage_run_dashboard_v1;approval_packet;stage_control_loop',
    'sync_artifact',
    'Callable manager entrypoint that runs one safe stage-control step without provider calls and writes a receipt/dashboard for the operator.'
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
