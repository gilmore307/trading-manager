-- Register stable Layer 3 TargetStateVector source/feature/model entrypoints.
-- These rows identify callable commands; ordinary importable source files remain
-- owned by source/data_feature/model/term registry rows.
INSERT INTO trading_registry (
  id,
  kind,
  key,
  payload_format,
  payload,
  path,
  applies_to,
  artifact_sync_policy,
  note
) VALUES
  (
    'scr_F3TSSRC',
    'script',
    'SOURCE_03_TARGET_STATE_BUILD',
    'command',
    'trading-data-source-03-target-state',
    '/root/projects/trading-data/src/data_source/source_03_target_state',
    'trading-data;source_03_target_state;feature_03_target_state_vector;target_state_vector_model',
    'sync_artifact',
    'Stable callable entrypoint for normalizing Layer 3 target-local observed bars/liquidity evidence into source_03_target_state rows. Raw symbol is retained only as source/audit/routing metadata.'
  ),
  (
    'scr_F3TSVGEN',
    'script',
    'FEATURE_03_TARGET_STATE_VECTOR_GENERATE',
    'command',
    'trading-data-feature-03-target-state-vector',
    '/root/projects/trading-data/src/data_feature/feature_03_target_state_vector',
    'trading-data;source_03_target_state;feature_03_target_state_vector;target_state_vector_model;model_03_target_state_vector',
    'sync_artifact',
    'Stable callable entrypoint for reading source_03_target_state plus optional Layer 1/2 context rows and writing feature_03_target_state_vector JSONB market/sector/target/cross-state blocks.'
  ),
  (
    'scr_M3TSVGEN',
    'script',
    'MODEL_03_TARGET_STATE_VECTOR_GENERATE',
    'command',
    'python3 scripts/models/model_03_target_state_vector/generate_model_03_target_state_vector.py',
    '/root/projects/trading-model/scripts/models/model_03_target_state_vector/generate_model_03_target_state_vector.py',
    'trading-model;target_state_vector_model;model_03_target_state_vector;feature_03_target_state_vector',
    'sync_artifact',
    'Stable callable entrypoint for generating deterministic model_03_target_state_vector rows from feature_03_target_state_vector evidence.'
  ),
  (
    'scr_M3TSVEVAL',
    'script',
    'MODEL_03_TARGET_STATE_VECTOR_EVALUATE_PROMOTION_EVIDENCE',
    'command',
    'python3 scripts/models/model_03_target_state_vector/evaluate_model_03_target_state_vector.py',
    '/root/projects/trading-model/scripts/models/model_03_target_state_vector/evaluate_model_03_target_state_vector.py',
    'trading-model;target_state_vector_model;model_03_target_state_vector;feature_03_target_state_vector;model_evaluation;promotion_evidence',
    'sync_artifact',
    'Stable callable entrypoint for building TargetStateVectorModel promotion evidence over market-only, market+sector, and market+sector+target-vector baselines.'
  ),
  (
    'scr_M3TSVREV',
    'script',
    'MODEL_03_TARGET_STATE_VECTOR_REVIEW_PROMOTION',
    'command',
    'python3 scripts/models/model_03_target_state_vector/review_target_state_vector_promotion.py',
    '/root/projects/trading-model/scripts/models/model_03_target_state_vector/review_target_state_vector_promotion.py',
    'trading-model;target_state_vector_model;model_03_target_state_vector;model_evaluation;promotion_review',
    'sync_artifact',
    'Stable callable conservative promotion-review wrapper. Fixture/local evidence must defer until real-data thresholds, split stability, baseline improvement, and leakage gates are reviewed and accepted.'
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
