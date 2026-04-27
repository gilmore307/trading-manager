-- Register implemented ThetaData option selection snapshot bundle path.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET path = 'trading-data/src/trading_data/data_sources/thetadata_option_selection_snapshot',
    artifact_sync_policy = 'sync_artifact',
    note = 'Implemented ThetaData option bundle for explicit-time point-in-time option-chain snapshots used to simulate contract selection from information visible at signal time; development output is final option_chain_snapshot JSON and durable storage direction is SQL JSONB'
WHERE kind = 'data_bundle'
  AND key = 'THETADATA_OPTION_SELECTION_SNAPSHOT';
