-- Register manager stage coverage gate over task_summary readiness.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_MGRSCOV001',
    'artifact_type',
    'MANAGER_STAGE_COVERAGE_V1',
    'text',
    'manager_stage_coverage_v1',
    'trading-manager/docs/95_task_system.md',
    'manager_model_training_workflow_state_v1;task_summary;ready_signal_v1;manager_request_v1',
    'sync_artifact',
    'Stage-level coverage report derived from manager task_summary. It distinguishes partial task readiness from full workflow-stage completion and is required before downstream workflow unlock.'
  ),
  (
    'scr_MGRSCOV001',
    'script',
    'MANAGER_STAGE_COVERAGE_CHECK',
    'text',
    'PYTHONPATH=src python3 scripts/tasks/check_stage_coverage.py --stage-id layer_01_market_regime.data_acquisition --start-month 2016-01 --end-month 2016-01 --expected-count 22',
    'trading-manager/scripts/tasks/check_stage_coverage.py',
    'manager_stage_coverage_v1;task_summary;manager_model_training_workflow_state_v1',
    'sync_artifact',
    'Checks SQL task_summary coverage for a workflow stage. Partial coverage writes evidence only; only full expected ready coverage sets can_unlock_downstream=true.'
  ),
  (
    'cfg_MGRSCOV001',
    'config',
    'MANAGER_STAGE_COVERAGE_UNLOCK_POLICY',
    'text',
    'task_level_ready_signal_not_stage_completion;partial_ready_blocks_downstream;full_expected_coverage_required;can_unlock_downstream_true_required',
    'trading-manager/docs/95_task_system.md',
    'manager_stage_coverage_v1;manager_model_training_workflow_state_v1;layer_01_market_regime.data_acquisition',
    'sync_artifact',
    'A workflow stage may move from ready to succeeded from SQL-derived evidence only when manager_stage_coverage_v1 reports status=ready and can_unlock_downstream=true. Example: 3/22 Layer 1 January 2016 provider receipts remain partial_ready.'
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
