-- Split Layer 2 dispersion/crowding semantics and register expanded Layer 3
-- target-state groups/scores. Keep routing/diagnostic/research names explicit so
-- downstream consumers do not treat them as ordinary alpha/action features.

UPDATE trading_registry
SET key = 'SECTOR_INTERNAL_DISPERSION_SCORE',
    payload = '2_sector_internal_dispersion_score',
    note = 'Layer 2 SectorContext state-vector value for sector internal dispersion/fragmentation evidence. Higher values indicate a less-clean handoff context, separate from crowding risk.',
    path = 'trading-model/src/models/model_02_sector_context/sector_context_state_contract.md',
    applies_to = 'model_02_sector_context;sector_context_state;sector_context_model;feature_02_sector_context',
    artifact_sync_policy = 'registry_only',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'fld_SCMV22007'
  AND kind = 'state_vector_value';

WITH new_values(id, key, payload_format, payload, path, applies_to, note) AS (
  VALUES
    ('fld_SCMV22020', 'SECTOR_CROWDING_RISK_SCORE', 'field_name', '2_sector_crowding_risk_score', 'trading-model/src/models/model_02_sector_context/sector_context_state_contract.md', 'model_02_sector_context;sector_context_state;sector_context_model;feature_02_sector_context', 'Layer 2 SectorContext state-vector value for sector crowding/co-movement pressure. Higher values indicate more one-factor/crowding risk, separate from internal dispersion.'),
    ('fld_TSV060', 'TARGET_PRICE_STATE', 'field_name', 'target_price_state', 'trading-model/src/models/model_03_target_state_vector/target_state_vector_contract.md', 'target_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model', 'TargetStateVector target-state group for completed-bar price anchors used by path labels and diagnostics; no future bars.'),
    ('fld_TSV061', 'TARGET_TREND_AGE_STATE', 'field_name', 'target_trend_age_state', 'trading-model/src/models/model_03_target_state_vector/target_state_vector_contract.md', 'target_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model', 'TargetStateVector target-state group for trend/state age, direction flip count, time since last direction flip, and persistence evidence.'),
    ('fld_TSV062', 'TARGET_EXHAUSTION_DECAY_STATE', 'field_name', 'target_exhaustion_decay_state', 'trading-model/src/models/model_03_target_state_vector/target_state_vector_contract.md', 'target_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model', 'TargetStateVector target-state group for momentum decay, volume/volatility exhaustion, trend-slope decay, and late-trend risk evidence.'),
    ('fld_TSV063', 'TARGET_PEER_RANK_STATE', 'field_name', 'target_peer_rank_state', 'trading-model/src/models/model_03_target_state_vector/target_state_vector_contract.md', 'target_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model', 'TargetStateVector target-state group for point-in-time peer/candidate-pool ranks of tradability qualities, not raw strength or identity.'),
    ('fld_TSV064', 'TARGET_SHORTABILITY_STATE', 'field_name', 'target_shortability_state', 'trading-model/src/models/model_03_target_state_vector/target_state_vector_contract.md', 'target_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model', 'TargetStateVector optional shortability/borrow/locate overlay group. May be null until a reviewed source exists; data policy optional_overlay_not_required_for_state_vector_v1.'),
    ('fld_TSV065', 'TARGET_EVENT_RISK_STATE', 'field_name', 'target_event_risk_state', 'trading-model/src/models/model_03_target_state_vector/target_state_vector_contract.md', 'target_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model', 'TargetStateVector optional event/news/halt/macro-risk overlay group. May be null until reviewed event sources exist; data policy optional_overlay_not_required_for_state_vector_v1.'),
    ('fld_TSV066', 'TARGET_DIRECTION_STRENGTH_SCORE_BY_WINDOW', 'field_name', '3_target_direction_strength_score_<window>', 'trading-model/src/models/model_03_target_state_vector/target_state_vector_contract.md', 'score_payload;target_state_vector;model_03_target_state_vector;target_state_vector_model;model_evaluation;promotion_evidence', 'TargetStateVector score family for absolute target direction-evidence strength by window. High can describe either a clean long or clean short state.'),
    ('fld_TSV067', 'TARGET_STATE_PERSISTENCE_SCORE_BY_WINDOW', 'field_name', '3_target_state_persistence_score_<window>', 'trading-model/src/models/model_03_target_state_vector/target_state_vector_contract.md', 'score_payload;target_state_vector;model_03_target_state_vector;target_state_vector_model;model_evaluation;promotion_evidence', 'TargetStateVector score family for direction-neutral state/trend persistence support by window.'),
    ('fld_TSV068', 'TARGET_EXHAUSTION_RISK_SCORE_BY_WINDOW', 'field_name', '3_target_exhaustion_risk_score_<window>', 'trading-model/src/models/model_03_target_state_vector/target_state_vector_contract.md', 'score_payload;target_state_vector;model_03_target_state_vector;target_state_vector_model;model_evaluation;promotion_evidence', 'TargetStateVector score family for direction-neutral late-trend/exhaustion/decay risk by window. Higher values indicate worse risk.'),
    ('trm_TSVDP001', 'TARGET_STATE_OPTIONAL_OVERLAY_NOT_REQUIRED_V1', 'text', 'optional_overlay_not_required_for_state_vector_v1', 'trading-model/src/models/model_03_target_state_vector/target_state_vector_contract.md', 'target_shortability_state;target_event_risk_state;feature_03_target_state_vector;target_state_vector_model', 'TargetStateVector data-policy value for optional overlay groups that may remain null until reviewed external sources exist.'),
    ('trm_TSVOI001', 'TARGET_STATE_UNRESOLVED_IMPLIED_RANGE_IDENTIFIER', 'text', '/implied/range', 'trading-model/src/models/model_03_target_state_vector/target_state_vector_contract.md', 'market_volatility_state;target_volatility_range_state;state_vector_feature_semantics_review', 'Opaque unresolved identifier retained for future source/feature mapping review; do not rewrite or infer provider semantics.'),
    ('trm_TSVOI002', 'TARGET_STATE_UNRESOLVED_STRESS_COST_IDENTIFIER', 'text', '/stress/cost', 'trading-model/src/models/model_03_target_state_vector/target_state_vector_contract.md', 'market_liquidity_stress_state;target_liquidity_tradability_state;state_vector_feature_semantics_review', 'Opaque unresolved identifier retained for future source/feature mapping review; do not rewrite or infer provider semantics.'),
    ('trm_TSVOI003', 'TARGET_STATE_UNRESOLVED_OPTIONABILITY_COST_IDENTIFIER', 'text', '/optionability/cost', 'trading-model/src/models/model_03_target_state_vector/target_state_vector_contract.md', 'sector_liquidity_tradability_state;target_liquidity_tradability_state;state_vector_feature_semantics_review', 'Opaque unresolved identifier retained for future source/feature mapping review; do not rewrite or infer provider semantics.')
)
INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
SELECT id, 'state_vector_value', key, payload_format, payload, path, applies_to, 'registry_only', note
FROM new_values
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
SET note = CASE id
      WHEN 'fld_TSV052' THEN 'TargetStateVector score family for direction-neutral state tradability by window. Stable short states can score highly; validation should use path/tradability outcomes, MFE/MAE balance, path efficiency, direction flips, transition rate, and liquidity/cost degradation rather than only forward return.'
      WHEN 'fld_TSV057' THEN 'TargetStateVector research/diagnostic embedding payload. It is not a first-version primary model feature and must not replace inspectable block fields without reviewed walk-forward fit/assign controls.'
      WHEN 'fld_TSV058' THEN 'TargetStateVector research/diagnostic state-cluster identifier. It is not a first-version primary model feature and must not leak target identity or future labels.'
      ELSE note
    END,
    updated_at = CURRENT_TIMESTAMP
WHERE id IN ('fld_TSV052', 'fld_TSV057', 'fld_TSV058')
  AND kind = 'state_vector_value';
