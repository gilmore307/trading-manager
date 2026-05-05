-- Register the Layer 3 reset from strategy-selection simulation to target state-vector construction.
-- The old strategy-selection source/feature/script remain legacy compatibility assets;
-- new cross-repository contracts should use target-state names.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'dbu_TSTATE03',
    'data_source',
    'SOURCE_03_TARGET_STATE',
    'text',
    'source_03_target_state',
    'trading-data/src/data_source/source_03_target_state',
    'trading-data;trading-model;target_state_vector_model;model_03_target_state_vector',
    'registry_only',
    '03 control-plane-facing target-local observed-input source contract for TargetStateVectorModel. New Layer 3 data requests should use source_03_target_state; source_03_strategy_selection remains a legacy compatibility implementation until migrated.'
  ),
  (
    'dki_TSVF001',
    'data_feature',
    'FEATURE_03_TARGET_STATE_VECTOR',
    'text',
    'feature_03_target_state_vector',
    'trading-data/src/data_feature/feature_03_target_state_vector',
    'trading-data;trading-model;trading-manager;source_03_target_state;target_state_vector_model;model_03_target_state_vector',
    'registry_only',
    'Active Layer 3 deterministic target state-vector feature contract. trading-manager issues reviewed requests, trading-data builds point-in-time market/sector/target/cross-state feature blocks under feature_03_target_state_vector, and trading-model consumes the output for TargetStateVectorModel training, evaluation, and promotion evidence.'
  ),
  (
    'trm_TSVMI01',
    'term',
    'TARGET_STATE_VECTOR_MODEL',
    'text',
    'target_state_vector_model',
    'trading-model/docs/90_system_model_architecture_rfc.md',
    'trading-model;trading-data;model_03_target_state_vector;feature_03_target_state_vector',
    'registry_only',
    'Accepted canonical Layer 3 model id. TargetStateVectorModel constructs anonymous target state vectors from market, sector, and target-local evidence before later trade/strategy decisions.'
  ),
  (
    'trm_M3TSV01',
    'term',
    'MODEL_03_TARGET_STATE_VECTOR',
    'text',
    'model_03_target_state_vector',
    'trading-model/docs/04_layer_03_target_state_vector.md',
    'trading-model;target_state_vector_model;feature_03_target_state_vector',
    'registry_only',
    'Accepted Layer 3 TargetStateVectorModel model-output surface name; primary physical output is expected under trading_model.model_03_target_state_vector after implementation acceptance.'
  ),
  (
    'trm_TSV001',
    'term',
    'TARGET_STATE_VECTOR',
    'text',
    'target_state_vector',
    'trading-model/docs/04_layer_03_target_state_vector.md',
    'trading-model;trading-data;target_state_vector_model;model_03_target_state_vector;feature_03_target_state_vector',
    'registry_only',
    'Layer 3 model-facing anonymous target state vector built from separately inspectable market, sector, target-local, and cross-state blocks; raw ticker/company identity stays outside fitting vectors.'
  ),
  (
    'trm_TSVFR01',
    'term',
    'TARGET_STATE_VECTOR_FEATURE_REQUEST',
    'text',
    'target_state_vector_feature_request',
    'trading-data/docs/04_layer_03_target_state_vector.md',
    'trading-manager;trading-data;trading-model;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model',
    'registry_only',
    'Manager-issued request for deterministic Layer 3 target state-vector feature production. The request supplies the reviewed window, anonymous candidate-universe reference, Layer 1/2 state references, and output target; labels, training, evaluation, and promotion decisions remain model-owned.'
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
SET applies_to = 'trading-data;trading-model;sector_context_model;model_03_target_state_vector;target_state_vector_model;anonymous_target_candidate_builder',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'SOURCE_02_TARGET_CANDIDATE_HOLDINGS';

UPDATE trading_registry
SET applies_to = 'trading-model;trading-data;sector_context_model;model_03_target_state_vector;target_state_vector_model',
    path = 'trading-model/src/models/model_03_target_state_vector/anonymous_target_candidate_builder/target_candidate_builder_contract.md',
    note = 'Layer 3 candidate-preparation sub-boundary before TargetStateVectorModel. It expands selected/prioritized sector or industry baskets from SectorContextModel into anonymous target candidates while keeping real ticker/company identity in audit/routing metadata outside model-facing fitting vectors.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'ANONYMOUS_TARGET_CANDIDATE_BUILDER';

UPDATE trading_registry
SET applies_to = 'trading-model;model_03_target_state_vector;target_state_vector_model;anonymous_target_candidate_builder',
    note = 'Model-facing anonymous target candidate feature vector consumed by TargetStateVectorModel; excludes ticker/company identity while carrying behavior, liquidity, market, sector, event, risk, and cost context.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'ANONYMOUS_TARGET_FEATURE_VECTOR';

UPDATE trading_registry
SET applies_to = 'trading-model;model_03_target_state_vector;target_state_vector_model;anonymous_target_candidate_builder',
    note = 'Stable anonymous identifier for a target candidate. Real symbols remain audit/routing metadata outside model-facing fitting vectors.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'TARGET_CANDIDATE_ID';

UPDATE trading_registry
SET note = 'Legacy compatibility Layer 3 StrategySelectionModel feature surface. Layer 3 has been reset to target state-vector construction; do not expand feature_03_strategy_selection as the active cross-repository boundary unless a later reviewed decision reactivates it.',
    artifact_sync_policy = 'registry_only',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'FEATURE_03_STRATEGY_SELECTION';

UPDATE trading_registry
SET note = 'Legacy compatibility StrategySelectionModel data source. New Layer 3 data contracts should use source_03_target_state; keep this row only to identify existing source_03_strategy_selection implementations during migration.',
    artifact_sync_policy = 'registry_only',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'SOURCE_03_STRATEGY_SELECTION';

UPDATE trading_registry
SET note = 'Legacy compatibility entrypoint for feature_03_strategy_selection SQL generation. Layer 3 active work has moved to target state-vector construction; do not expand this script as the active Layer 3 handoff.',
    artifact_sync_policy = 'registry_only',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'FEATURE_03_STRATEGY_SELECTION_GENERATE';

UPDATE trading_registry
SET note = 'Legacy compatibility request term for the old StrategySelectionModel feature run. New manager-issued Layer 3 requests should use target_state_vector_feature_request.',
    artifact_sync_policy = 'registry_only',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'STRATEGY_SELECTION_FEATURE_REQUEST';

UPDATE trading_registry
SET applies_to = CASE
    WHEN applies_to IS NULL OR applies_to = '' THEN 'source_03_target_state'
    WHEN applies_to LIKE '%source_03_target_state%' THEN applies_to
    ELSE applies_to || ';source_03_target_state'
  END,
  updated_at = CURRENT_TIMESTAMP
WHERE applies_to LIKE '%source_03_strategy_selection%'
  AND kind IN ('field', 'identity_field', 'temporal_field', 'classification_field', 'path_field', 'text_field', 'parameter_field');
