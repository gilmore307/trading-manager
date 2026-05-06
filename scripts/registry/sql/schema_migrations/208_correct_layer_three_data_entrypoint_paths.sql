-- Correct Layer 3 data script registry rows to point at callable module entrypoints
-- rather than package directories.
UPDATE trading_registry
SET path = '/root/projects/trading-data/src/data_source/source_03_target_state/__main__.py',
    note = 'Stable callable entrypoint for normalizing Layer 3 target-local observed bars/liquidity evidence into source_03_target_state rows. Raw symbol is retained only as source/audit/routing metadata.',
    updated_at = CURRENT_TIMESTAMP
WHERE kind = 'script'
  AND key = 'SOURCE_03_TARGET_STATE_BUILD';

UPDATE trading_registry
SET path = '/root/projects/trading-data/src/data_feature/feature_03_target_state_vector/__main__.py',
    note = 'Stable callable entrypoint for reading source_03_target_state plus optional Layer 1/2 context rows and writing feature_03_target_state_vector JSONB market/sector/target/cross-state blocks.',
    updated_at = CURRENT_TIMESTAMP
WHERE kind = 'script'
  AND key = 'FEATURE_03_TARGET_STATE_VECTOR_GENERATE';
