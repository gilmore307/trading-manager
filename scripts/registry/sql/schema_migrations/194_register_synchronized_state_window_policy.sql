-- Register synchronized state-window metadata introduced by the TargetStateVector V1
-- model/data implementation. The window set was already registered as a config row;
-- this migration renames it from trailing-window wording to synchronized-window wording
-- and registers the shared metadata fields emitted by feature rows.

UPDATE trading_registry
SET key = 'TARGET_STATE_VECTOR_SYNCHRONIZED_STATE_WINDOWS',
    note = 'Sparse TargetStateVector V1 synchronized state-observation windows for market, sector, target, and cross-state blocks. Current windows are 5min, 15min, 60min, and 390min; these are state windows, not strategy variants.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'TARGET_STATE_VECTOR_TRAILING_STATE_WINDOWS';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'fld_TSV011',
    'field',
    'STATE_OBSERVATION_WINDOWS',
    'field_name',
    'state_observation_windows',
    NULL,
    'model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model;market_state_features;sector_state_features;target_state_features;cross_state_features',
    'registry_only',
    'Per-block TargetStateVector V1 metadata listing the synchronized state-observation windows used by market, sector, target, and cross-state feature blocks for a row.'
  ),
  (
    'fld_TSV012',
    'field',
    'STATE_WINDOW_SYNC_POLICY',
    'field_name',
    'state_window_sync_policy',
    NULL,
    'model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model;market_state_features;sector_state_features;target_state_features;cross_state_features',
    'registry_only',
    'Per-block TargetStateVector V1 metadata naming the synchronization policy that market, sector, and target blocks must share identical observation windows and cross-state comparisons may only compare matching window labels.'
  ),
  (
    'cfg_TSVV001',
    'config',
    'TARGET_STATE_VECTOR_VERSION_DEFAULT',
    'text',
    'target_state_vector_v1',
    'trading-model/src/models/model_03_target_state_vector/contract.py',
    'model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model;target_state_vector_version',
    'registry_only',
    'Default TargetStateVector V1 contract/config version value emitted as target_state_vector_version by current Layer 3 target-state feature rows.'
  ),
  (
    'cfg_TSVP001',
    'config',
    'TARGET_STATE_VECTOR_WINDOW_SYNC_POLICY',
    'text',
    'market_sector_target_blocks_must_share_identical_observation_windows',
    'trading-model/src/models/model_03_target_state_vector/target_state_vector_contract.md',
    'model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model;state_window_sync_policy',
    'registry_only',
    'Accepted TargetStateVector V1 synchronization-policy value: market, sector, and target feature blocks must share identical state-observation windows; cross-state features may compare only matching window labels.'
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
