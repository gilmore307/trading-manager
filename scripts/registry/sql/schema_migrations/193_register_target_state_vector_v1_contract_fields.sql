-- Register shared TargetStateVector V1 row keys, feature blocks, and sparse window defaults
-- introduced by trading-model e21f631 and trading-data cda745b.

UPDATE trading_registry
SET key = 'AVAILABLE_TIME',
    applies_to = CASE
      WHEN applies_to LIKE '%model_03_target_state_vector%' THEN applies_to
      ELSE applies_to || ';model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model'
    END,
    note = 'Timestamp when evidence, feature rows, or model outputs became visible for point-in-time use. Temporal value format: ISO 8601; normalized final outputs use America/New_York semantics unless explicitly reviewed otherwise.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'fld_STKEX011';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'fld_TSV001',
    'temporal_field',
    'TRADEABLE_TIME',
    'field_name',
    'tradeable_time',
    NULL,
    'model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model',
    'registry_only',
    'Earliest realistic time a downstream decision may trade from a TargetStateVectorModel state row. Temporal value format: ISO 8601; normalized final outputs use America/New_York semantics unless explicitly reviewed otherwise.'
  ),
  (
    'fld_TSV002',
    'field',
    'TARGET_STATE_VECTOR_VERSION',
    'field_name',
    'target_state_vector_version',
    NULL,
    'model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model',
    'registry_only',
    'Reviewed TargetStateVector V1 contract/config version carried by feature and model rows; use target_state_vector_version rather than generic feature_vector_version for the Layer 3 target-state surface.'
  ),
  (
    'fld_TSV003',
    'field',
    'MARKET_CONTEXT_STATE_REF',
    'field_name',
    'market_context_state_ref',
    NULL,
    'model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model;model_01_market_regime',
    'registry_only',
    'Reference from a Layer 3 target-state row to the Layer 1 market context state used as point-in-time input.'
  ),
  (
    'fld_TSV004',
    'field',
    'SECTOR_CONTEXT_STATE_REF',
    'field_name',
    'sector_context_state_ref',
    NULL,
    'model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model;model_02_sector_context',
    'registry_only',
    'Reference from a Layer 3 target-state row to the Layer 2 sector context state used as point-in-time input.'
  ),
  (
    'fld_TSV005',
    'field',
    'TARGET_STATE_VECTOR_REF',
    'field_name',
    'target_state_vector_ref',
    NULL,
    'model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model',
    'registry_only',
    'Stable reference or hash for the model-facing target state-vector payload.'
  ),
  (
    'fld_TSV006',
    'field',
    'SOURCE_RUN_REF',
    'field_name',
    'source_run_ref',
    NULL,
    'feature_03_target_state_vector;source_03_target_state',
    'registry_only',
    'Reference from a deterministic feature row to the source/input run or request evidence used to build it.'
  ),
  (
    'fld_TSV007',
    'field',
    'MARKET_STATE_FEATURES',
    'field_name',
    'market_state_features',
    NULL,
    'model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model',
    'registry_only',
    'Inspectable TargetStateVector V1 feature block containing broad market-state evidence inherited or projected from Layer 1.'
  ),
  (
    'fld_TSV008',
    'field',
    'SECTOR_STATE_FEATURES',
    'field_name',
    'sector_state_features',
    NULL,
    'model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model',
    'registry_only',
    'Inspectable TargetStateVector V1 feature block containing sector/industry context inherited or projected from Layer 2.'
  ),
  (
    'fld_TSV009',
    'field',
    'TARGET_STATE_FEATURES',
    'field_name',
    'target_state_features',
    NULL,
    'model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model',
    'registry_only',
    'Inspectable TargetStateVector V1 feature block containing anonymous target-local board/tape, liquidity, and data-quality evidence.'
  ),
  (
    'fld_TSV010',
    'field',
    'CROSS_STATE_FEATURES',
    'field_name',
    'cross_state_features',
    NULL,
    'model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model',
    'registry_only',
    'Inspectable TargetStateVector V1 feature block containing target-vs-market and target-vs-sector relationship evidence.'
  ),
  (
    'cfg_TSVW001',
    'config',
    'TARGET_STATE_VECTOR_TRAILING_STATE_WINDOWS',
    'text',
    '5min;15min;60min;390min',
    'trading-model/src/models/model_03_target_state_vector/target_state_vector_contract.md',
    'model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model',
    'registry_only',
    'Sparse TargetStateVector V1 trailing state-observation windows for return, volatility, volume, liquidity, and relative-strength summaries. These are state windows, not strategy variants.'
  )
ON CONFLICT (id) DO UPDATE SET
    kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = CURRENT_TIMESTAMP;

UPDATE trading_registry
SET kind = 'identity_field',
    payload_format = 'field_name',
    applies_to = 'trading-model;trading-data;model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model;anonymous_target_candidate_builder',
    note = 'Opaque anonymous row key for a TargetStateVectorModel candidate; never use target_candidate_id as a categorical fitting feature. Real symbols remain audit/routing metadata outside model-facing vectors.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'TARGET_CANDIDATE_ID';
