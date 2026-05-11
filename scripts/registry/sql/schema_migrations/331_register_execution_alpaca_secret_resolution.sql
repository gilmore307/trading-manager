-- Register execution-side Alpaca live-observe secret resolution.

UPDATE trading_registry
SET applies_to = 'trading-data;trading-execution',
    note = 'source-level secret JSON alias for Alpaca credentials and endpoint; JSON keys include api_key, secret_key, and endpoint; secret values are stored outside Git; used by trading-data historical acquisition and trading-execution read-only realtime observe',
    updated_at = NOW()
WHERE key = 'ALPACA_SECRET_ALIAS';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'cfg_EXEC_ALPACA001',
  'config',
  'EXECUTION_ALPACA_LIVE_OBSERVE_SECRET_RESOLUTION_POLICY',
  'text',
  'prefer_runtime_env_vars_then_registered_source_secret_json;secret_values_never_written_to_repo_or_receipts;read_only_market_data_observe_only',
  'trading-execution/src/trading_execution/market_data/live_provider.py',
  'trading-execution;alpaca;realtime_live_observe;source_secret_file_schema;ALPACA_SECRET_ALIAS',
  'sync_artifact',
  'Execution-side Alpaca live observe may use injected APCA/ALPACA environment variables or the registered /root/secrets/alpaca.json source secret JSON. This is credential resolution for read-only market-data observation only and does not authorize model activation, broker execution, order construction, or account mutation.'
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
