-- Register automatic next-work selection for the historical scheduler service.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_MASR004',
    'config',
    'MANAGER_HISTORICAL_SCHEDULER_AUTO_SELECT_NEXT_WORK',
    'text',
    'auto_select_next_work',
    'trading-manager/src/trading_manager_tasks/scheduler_daemon.py',
    'trading-manager;scheduler;historical_training;daemon;manager_historical_work_selection_v1;manager_scheduler_daemon_state_v1',
    'sync_artifact',
    'Daemon option that reviews completed/open month-scoped workflow checkpoints, resumes the earliest open month, or selects the next chronological month after the latest completed checkpoint without owner continuation prompts.'
  ),
  (
    'trm_MHWS001',
    'term',
    'MANAGER_HISTORICAL_WORK_SELECTION',
    'text',
    'manager_historical_work_selection_v1',
    'trading-manager/src/trading_manager_tasks/scheduler_daemon.py',
    'trading-manager;scheduler;historical_training;daemon;workflow_state;chronological_forward',
    'sync_artifact',
    'Service bootstrap decision contract for choosing the next historical workflow month from durable completed/open workflow state before running scheduler ticks.'
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

UPDATE trading_registry
SET payload = 'PYTHONPATH=src python3 scripts/tasks/run_automation_scheduler_daemon.py --execute-safe-preparation --execute-safe-offline-stages --auto-select-next-work --advance-month-on-complete',
    applies_to = 'trading-manager;scheduler;historical_training;daemon;manager_scheduler_daemon_state_v1;manager_scheduler_decision_v1;manager_historical_work_selection_v1;chronological_month_advance',
    note = 'Runs the persistent system-service-owned historical modeling scheduler daemon. The daemon audits completed/open workflow checkpoints, selects the next planned chronological month, loops over capacity-aware scheduler ticks, persists resume state, writes decision JSONL, enforces a single-instance lock, executes safe/offline stages, advances the chronological month cursor after completion, and preserves provider/model/broker/storage gates.',
    updated_at = NOW()
WHERE id = 'scr_MASD001';

UPDATE trading_registry
SET note = 'Reviewed systemd template for host-level boot autostart and Restart=always supervision of the historical modeling scheduler daemon. The template enables automatic next-work selection, safe preparation, safe offline stages, and automatic chronological month advancement; committing it does not install or enable the host service.',
    applies_to = 'trading-manager;scheduler;historical_training;daemon;systemd;boot_autostart;manager_historical_work_selection_v1;chronological_month_advance',
    updated_at = NOW()
WHERE id = 'scr_MASV001';
