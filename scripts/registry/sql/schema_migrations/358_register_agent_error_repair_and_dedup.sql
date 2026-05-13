-- Register safe auto-repair runner, alert timestamps, and dedup behavior.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_AGENTERR004',
    'artifact_type',
    'SERVER_ERROR_CATALOG_OCCURRENCE',
    'text',
    'server_error_catalog_occurrence',
    'trading-manager/storage/runtime/agent_error_handling/server_error_catalog.jsonl',
    'server_wide_agent_error_handoff;deduplication;human_error_number;discord_alert',
    'sync_artifact',
    'Append-only occurrence row for a duplicate server error within the dedup window. It reuses the original ERR number rather than allocating a new owner-facing error.'
  ),
  (
    'cfg_AGENTERR005',
    'config',
    'MANAGER_AGENT_ERROR_DEDUP_POLICY',
    'text',
    'fingerprint_excludes_occurrence_time_and_log_paths;dedup_window_seconds=3600;duplicate_notifications_suppressed_by_default',
    'trading-manager/src/trading_manager_tasks/agent_error_handler.py',
    'server_wide_agent_error_handoff;deduplication;discord_alert;owner_visibility',
    'sync_artifact',
    'Repeated errors with the same fingerprint inside the dedup window reuse the same ERR number and suppress duplicate Discord notifications unless explicitly overridden.'
  ),
  (
    'cfg_AGENTERR006',
    'config',
    'MANAGER_AGENT_ERROR_ALERT_TIME_POLICY',
    'text',
    'discord_alerts_include_occurred_and_recorded_timestamps_in_utc_and_america_new_york',
    'trading-manager/src/trading_manager_tasks/agent_error_handler.py',
    'server_wide_agent_error_handoff;discord_alert;timestamp;owner_visibility',
    'sync_artifact',
    'Discord error alerts include occurred and recorded timestamps in UTC and America/New_York so owner follow-up can correlate messages with logs.'
  ),
  (
    'scr_AGENTERR003',
    'script',
    'MANAGER_SAFE_ERROR_REPAIR_RUNNER',
    'command',
    '/usr/bin/python3 /root/projects/trading-manager/scripts/tasks/run_safe_error_repair.py',
    '/root/projects/trading-manager/scripts/tasks/run_safe_error_repair.py',
    'server_wide_agent_error_handoff;safe_auto_repair;scheduler_dead_pid_lock;no_provider_calls;no_broker_mutation',
    'sync_artifact',
    'Reviewed deterministic repair runner. It currently removes only scheduler locks whose recorded PID is confirmed dead; unknown errors remain diagnosis-only.'
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
