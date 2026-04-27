-- Register implemented ThetaData option primary tracking bundle path.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET path = 'trading-data/src/trading_data/data_sources/thetadata_option_primary_tracking',
    artifact_sync_policy = 'sync_artifact',
    note = 'Implemented ThetaData option bundle for specified-contract primary tracking; caller supplies contract and timeframe, transient 1Sec OHLC rows are aggregated to final option_bar CSV, and contract selection remains model work'
WHERE kind = 'data_bundle'
  AND key = 'THETADATA_OPTION_PRIMARY_TRACKING';
