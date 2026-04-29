-- Move model-input config registry from a global data_bundles/configs file to bundle-local config.json files.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET key = 'DATA_BUNDLES_GLOBAL_CONFIG_DEPRECATED',
    payload_format = 'text',
    payload = 'deprecated',
    path = NULL,
    applies_to = 'trading-data;data_bundles',
    artifact_sync_policy = 'registry_only',
    note = 'Deprecated placeholder: data bundle configs now live inside each bundle folder as config.json rather than under data_bundles/configs/'
WHERE id = 'cfg_DATABUNDLES';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('cfg_STKETFEX', 'config', 'STOCK_ETF_EXPOSURE_BUNDLE_CONFIG', 'json', '{"config":"bundle-local"}', 'trading-data/src/trading_data/data_bundles/stock_etf_exposure/config.json', 'trading-data;stock_etf_exposure;security_selection_model_inputs', 'sync_artifact', 'Bundle-local config for stock_etf_exposure, including ETF universe entries, issuer labels, desired grains, and default ETF score hooks'),
  ('cfg_EQABNACT', 'config', 'EQUITY_ABNORMAL_ACTIVITY_BUNDLE_CONFIG', 'json', '{"config":"bundle-local"}', 'trading-data/src/trading_data/data_bundles/equity_abnormal_activity/config.json', 'trading-data;equity_abnormal_activity;event_overlay_model_inputs', 'sync_artifact', 'Bundle-local config for equity_abnormal_activity detector defaults including grain, lookback, thresholds, and model_standard')
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note;
