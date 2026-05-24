-- Switch server-error repair handoff from OpenClaw agent CLI to Codex CLI.

UPDATE trading_registry
SET applies_to = 'server_wide_agent_error_handoff;codex_cli;agent_diagnosis;agent_repair;no_delivery;server-error-repair',
    note = 'Reviewed runner that passes server_error_agent_request JSON to Codex CLI with the server-error-repair skill and wraps the resulting turn as agent_error_diagnosis. It is the actual agent bridge; deterministic safe_error_repair remains a narrow fallback runner.',
    updated_at = NOW()
WHERE key = 'MANAGER_AGENT_ERROR_AGENT_RUNNER';

UPDATE trading_registry
SET payload = 'codex_cli_gpt_5_5_runner',
    applies_to = 'server_wide_agent_error_handoff;codex_cli;systemd_env;server-error-repair',
    note = 'Historical scheduler server-error handoff defaults to Codex CLI using gpt-5.5 and the server-error-repair skill, not the deterministic safe_error_repair runner. The safe runner is retained for explicit narrow deterministic repair tests.',
    updated_at = NOW()
WHERE key = 'MANAGER_AGENT_ERROR_DEFAULT_RUNNER';
