-- Register first manager automation scheduler tick implementation.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_MAST001',
    'script',
    'MANAGER_AUTOMATION_SCHEDULER_RUN',
    'text',
    'PYTHONPATH=src python3 scripts/tasks/run_automation_scheduler.py',
    'trading-manager/scripts/tasks/run_automation_scheduler.py',
    'trading-manager;scheduler;historical_training;layer_01_market_regime;manager_scheduler_decision_v1',
    'sync_artifact',
    'Runs one capacity-aware scheduler tick. It applies regular-trading-day market-hours protection and resource gates, then reports or executes safe offline Layer 1 task-key preparation without provider dispatch, model activation, or broker execution.'
  ),
  (
    'art_MSDV001',
    'artifact_type',
    'MANAGER_SCHEDULER_DECISION_V1',
    'text',
    'manager_scheduler_decision_v1',
    'trading-manager/src/trading_manager_tasks/scheduler.py',
    'trading-manager;scheduler;task_summary;manager_request_v1;ready_signal_v1',
    'sync_artifact',
    'One scheduler tick decision artifact: records allowed/backoff/executed status, explicit reason code, market-hours/resource gate state, selected work, command preview, and safety counters proving no provider/model/broker side effects for safe preparation.'
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
