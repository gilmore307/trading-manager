-- Register source-existing bootstrap as a required startup feature of the
-- historical-modeling scheduler service.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_MASR005',
    'config',
    'MANAGER_HISTORICAL_SCHEDULER_SOURCE_EXISTING_BOOTSTRAP',
    'text',
    'source_existing_bootstrap_enabled_by_default',
    'trading-manager/src/trading_manager_tasks/scheduler_daemon.py;trading-manager/src/trading_manager_tasks/source_existing_bootstrap.py',
    'trading-manager;scheduler;historical_modeling;daemon;startup;source_existing_bootstrap;manager_source_existing_bootstrap_v1;manager_stage_coverage',
    'sync_artifact',
    'Required startup behavior for the historical-modeling scheduler service: every daemon start inspects durable trading_data.source_* tables and seeds data-acquisition coverage from already-existing source rows before automatic work selection. This prevents clean-start deletion of generated request/receipt/control-plane rows from triggering unnecessary provider redownloads.'
  ),
  (
    'trm_MHSB001',
    'term',
    'MANAGER_SOURCE_EXISTING_BOOTSTRAP',
    'text',
    'manager_source_existing_bootstrap_v1',
    'trading-manager/src/trading_manager_tasks/source_existing_bootstrap.py',
    'trading-manager;scheduler;historical_modeling;source_existing_bootstrap;source_01_market_regime;source_03_target_state;source_09_event_risk_governor',
    'sync_artifact',
    'Startup bootstrap summary contract proving which preserved source rows satisfy historical data-acquisition stages without provider calls, model activation, broker execution, or storage lifecycle mutation.'
  ),
  (
    'scr_MASB001',
    'script',
    'MANAGER_SOURCE_EXISTING_BOOTSTRAP_INSPECT',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/bootstrap_existing_source_state.py',
    'trading-manager/scripts/tasks/bootstrap_existing_source_state.py;trading-manager/src/trading_manager_tasks/source_existing_bootstrap.py',
    'trading-manager;scheduler;historical_modeling;source_existing_bootstrap;inspection;dry_run;manager_source_existing_bootstrap_v1',
    'sync_artifact',
    'Operational inspection wrapper for source-existing bootstrap. Dry-run by default; writes workflow-state source coverage only with --write. It performs no provider calls, model activation, broker/account mutation, or storage lifecycle mutation.'
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
    applies_to = 'trading-manager;scheduler;historical_modeling;daemon;manager_scheduler_daemon_state_v1;manager_scheduler_decision_v1;manager_historical_work_selection_v1;chronological_month_advance;manager_source_existing_bootstrap_v1',
    note = 'Runs the persistent system-service-owned historical modeling scheduler daemon. Every daemon start first runs source-existing bootstrap, then audits completed/open workflow checkpoints, selects the next planned chronological month, loops over capacity-aware scheduler ticks, persists resume state, writes decision JSONL, enforces a single-instance lock, executes safe/offline stages, advances the chronological month cursor after completion, and preserves provider/model/broker/storage gates.',
    updated_at = NOW()
WHERE id = 'scr_MASD001';

UPDATE trading_registry
SET note = 'Reviewed systemd template for host-level boot autostart and Restart=always supervision of the historical modeling scheduler daemon. The template uses the daemon default source-existing bootstrap on every service start, then enables automatic next-work selection, safe preparation, safe offline stages, and automatic chronological month advancement; committing the template does not install or enable the host service.',
    applies_to = 'trading-manager;scheduler;historical_modeling;daemon;systemd;boot_autostart;manager_source_existing_bootstrap_v1;manager_historical_work_selection_v1;chronological_month_advance',
    updated_at = NOW()
WHERE id = 'scr_MASV001';
