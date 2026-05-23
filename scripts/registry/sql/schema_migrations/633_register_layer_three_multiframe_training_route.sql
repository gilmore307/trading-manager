-- Register Layer 3 multi-frame state and training-label route names.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'fld_TSV060',
    'field',
    'TARGET_STATE_MULTI_FRAME_STATE',
    'field_name',
    'multi_frame_state',
    'trading-model/src/models/model_03_target_state_vector/target_state_vector_contract.md',
    'feature_03_target_state_vector;target_state_vector;market_state_features;sector_state_features;target_state_features;cross_state_features;model_03_target_state_vector;target_state_vector_model',
    'registry_only',
    'Layer 3 feature-block map keyed by synchronized state window. It is the canonical multi-frame feature route for market, sector, target, and cross-state context, not a downstream action variant.'
  ),
  (
    'trm_TSVLBL001',
    'term',
    'TARGET_STATE_LABEL_FUTURE_TRADEABLE_PATH',
    'text',
    'future_tradeable_path',
    'trading-model/src/models/model_03_target_state_vector/target_state_vector_contract.md',
    'model_eval_label;model_03_target_state_vector;target_state_vector_model;path_quality;training_only',
    'registry_only',
    'Layer 3 training/evaluation label family for future path quality using path efficiency, MFE/MAE balance, and direction-flip penalty. It is training-only and must not join inference features.'
  ),
  (
    'trm_TSVLBL002',
    'term',
    'TARGET_STATE_LABEL_FORWARD_PATH_RISK',
    'text',
    'forward_path_risk',
    'trading-model/src/models/model_03_target_state_vector/target_state_vector_contract.md',
    'model_eval_label;model_03_target_state_vector;target_state_vector_model;path_risk;training_only',
    'registry_only',
    'Layer 3 training/evaluation label family for adverse future path risk, chop, flips, and MFE/MAE degradation. It is training-only and high values mean worse risk.'
  ),
  (
    'trm_TSVLBL003',
    'term',
    'TARGET_STATE_LABEL_LIQUIDITY_TRADABILITY_OUTCOME',
    'text',
    'liquidity_tradability_outcome',
    'trading-model/src/models/model_03_target_state_vector/target_state_vector_contract.md',
    'model_eval_label;model_03_target_state_vector;target_state_vector_model;tradability_outcome;training_only',
    'registry_only',
    'Layer 3 training/evaluation label family for whether liquidity and tradability remain usable across the future label horizon.'
  ),
  (
    'trm_TSVLBL004',
    'term',
    'TARGET_STATE_LABEL_STATE_TRANSITION_QUALITY',
    'text',
    'state_transition_quality',
    'trading-model/src/models/model_03_target_state_vector/target_state_vector_contract.md',
    'model_eval_label;model_03_target_state_vector;target_state_vector_model;state_transition;training_only',
    'registry_only',
    'Layer 3 training/evaluation label family for whether the future target state preserves or cleanly transitions from the current state without noisy sign flips.'
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
