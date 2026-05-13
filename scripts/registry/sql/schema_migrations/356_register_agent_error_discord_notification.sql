-- Register Discord notification behavior for server-wide agent error handoffs.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_AGENTERR002',
    'config',
    'MANAGER_AGENT_ERROR_DISCORD_NOTIFICATION_TARGET',
    'text',
    'discord_server=1480186849241731084;discord_channel=1504100135200620665;target=channel:1504100135200620665',
    '/root/projects/trading-manager/deploy/systemd/trading-manager-historical-scheduler.env',
    'server_wide_agent_error_handoff;discord_alert;owner_visibility;openclaw_message_send',
    'sync_artifact',
    'Reviewed host notification target for server-wide error handoff alerts. Error artifacts remain durable source of truth; Discord delivery is best-effort owner visibility.'
  ),
  (
    'cfg_AGENTERR003',
    'config',
    'MANAGER_AGENT_ERROR_DISCORD_NOTIFICATION_POLICY',
    'text',
    'best_effort_notify_after_artifact_write;notification_failure_must_not_block_error_artifacts_or_diagnosis_queue',
    'trading-manager/src/trading_manager_tasks/agent_error_handler.py',
    'server_wide_agent_error_handoff;discord_alert;failure_is_nonblocking',
    'sync_artifact',
    'Discord alerting for server errors is best-effort and must not block request/diagnosis artifact creation, queued diagnosis, or safe failure handling.'
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
