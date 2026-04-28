-- Move implemented model-input orchestration paths from data_sources to data_bundles.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET path = 'trading-data/src/trading_data/data_bundles/stock_etf_exposure',
    note = 'Implemented manager-facing derived model-input bundle that converts saved ETF holdings snapshots and ETF/sector/theme config into point-in-time stock_etf_exposure CSV rows'
WHERE id = 'dbu_STKETFEX';

UPDATE trading_registry
SET path = 'trading-data/src/trading_data/data_bundles/equity_abnormal_activity',
    note = 'Implemented manager-facing derived event bundle that detects abnormal equity/ETF return, volume, gap, relative-strength, and liquidity activity from saved Alpaca bar/liquidity CSV inputs and bundle config'
WHERE id = 'dbu_EQABNACT';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('cfg_DATABUNDLES', 'config', 'DATA_BUNDLES_MODEL_INPUT_CONFIG', 'json', '{"config":"model_inputs"}', 'trading-data/src/trading_data/data_bundles/configs/model_inputs.json', 'trading-data;data_bundles;model_inputs', 'sync_artifact', 'Config-backed parameters for model-input data bundles, including ETF universe entries, issuer labels, data grains, and detector defaults')
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note;
