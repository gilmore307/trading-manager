-- Register implemented derived bundles for model input and event overlay data products.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('dbu_STKETFEX', 'data_bundle', 'STOCK_ETF_EXPOSURE_BUNDLE', 'text', 'stock_etf_exposure', 'trading-data/src/trading_data/data_sources/stock_etf_exposure', 'trading-data;security_selection_model_inputs;stock_etf_exposure', 'sync_artifact', 'Implemented derived model-input bundle that converts saved ETF holdings snapshots and ETF/sector/theme scores into point-in-time stock_etf_exposure CSV rows'),
  ('dbu_EQABNACT', 'data_bundle', 'EQUITY_ABNORMAL_ACTIVITY_BUNDLE', 'text', 'equity_abnormal_activity', 'trading-data/src/trading_data/data_sources/equity_abnormal_activity', 'trading-data;event_overlay_model_inputs;equity_abnormal_activity_event', 'sync_artifact', 'Implemented derived event bundle that detects abnormal equity/ETF return, volume, gap, relative-strength, and liquidity activity from saved Alpaca bar/liquidity CSV inputs')
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note;
