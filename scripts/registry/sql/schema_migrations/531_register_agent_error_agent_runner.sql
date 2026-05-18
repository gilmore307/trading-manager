-- Register the real OpenClaw-agent runner for server error handoffs.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_AGENTERR004',
    'script',
    'MANAGER_AGENT_ERROR_AGENT_RUNNER',
    'command',
    '/usr/bin/python3 /root/projects/trading-manager/scripts/tasks/run_agent_error_agent.py',
    '/root/projects/trading-manager/scripts/tasks/run_agent_error_agent.py',
    'server_wide_agent_error_handoff;openclaw_agent;agent_diagnosis;agent_repair;no_delivery',
    'sync_artifact',
    'Reviewed runner that passes server_error_agent_request JSON to the OpenClaw project agent and wraps the resulting turn as agent_error_diagnosis. It is the actual agent bridge; deterministic safe_error_repair remains a narrow fallback runner.'
  ),
  (
    'cfg_AGENTERR007',
    'config',
    'MANAGER_AGENT_ERROR_DEFAULT_RUNNER',
    'text',
    'openclaw_agent_runner',
    '/root/projects/trading-manager/deploy/systemd/trading-manager-historical-scheduler.env',
    'server_wide_agent_error_handoff;openclaw_agent;systemd_env',
    'sync_artifact',
    'Historical scheduler server-error handoff defaults to the OpenClaw agent runner, not the deterministic safe_error_repair runner. The safe runner is retained for explicit narrow deterministic repair tests.'
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
