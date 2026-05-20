-- Register execution realtime runtime check timer template.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_EXECREAL001',
    'config',
    'EXECUTION_REALTIME_RUNTIME_CHECK_TIMER',
    'text',
    'trading-execution-realtime-runtime-check.timer;OnUnitActiveSec=60s',
    'trading-execution/deploy/systemd/trading-execution-realtime-runtime-check.service;trading-execution/deploy/systemd/trading-execution-realtime-runtime-check.timer',
    'trading-execution;systemd;realtime_trading_runtime;status_check;active_model_pointer',
    'sync_artifact',
    'Systemd timer template that refreshes execution_realtime_trading_runtime_status every minute. It is safe before model promotion because missing active model pointer is a waiting state and the service performs no provider, model, broker, order-submit, or account mutation work.'
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
