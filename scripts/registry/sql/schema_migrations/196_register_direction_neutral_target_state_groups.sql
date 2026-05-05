-- Register direction-neutral TargetStateVector V1 group names that are now shared
-- between trading-model and trading-data feature generation.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'fld_TSV015',
    'field',
    'SECTOR_RELATIVE_DIRECTION_STATE',
    'field_name',
    'sector_relative_direction_state',
    NULL,
    'sector_state_features;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model;model_02_sector_context',
    'registry_only',
    'TargetStateVector sector-state group for signed sector-vs-market direction evidence and handoff bias; direction sign is separate from quality/tradability.'
  ),
  (
    'fld_TSV016',
    'field',
    'SECTOR_TREND_QUALITY_STABILITY_STATE',
    'field_name',
    'sector_trend_quality_stability_state',
    NULL,
    'sector_state_features;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model;model_02_sector_context',
    'registry_only',
    'TargetStateVector sector-state group for sector trend quality, stability, chop/noise, and transition-risk context.'
  ),
  (
    'fld_TSV017',
    'field',
    'TARGET_DIRECTION_RETURN_SHAPE',
    'field_name',
    'target_direction_return_shape',
    NULL,
    'target_state_features;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model',
    'registry_only',
    'TargetStateVector target-state group for signed current-state direction evidence and trailing return shape across synchronized state windows.'
  ),
  (
    'fld_TSV018',
    'field',
    'TARGET_TREND_QUALITY_STATE',
    'field_name',
    'target_trend_quality_state',
    NULL,
    'target_state_features;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model',
    'registry_only',
    'TargetStateVector target-state group for target trend sign, structural quality, slope/alignment, and persistence independent of final action.'
  ),
  (
    'fld_TSV019',
    'field',
    'TARGET_LIQUIDITY_TRADABILITY_STATE',
    'field_name',
    'target_liquidity_tradability_state',
    NULL,
    'target_state_features;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model',
    'registry_only',
    'TargetStateVector target-state group for spread, quote coverage, capacity, slippage proxy, borrow/shortability where applicable, and practical tradability diagnostics.'
  ),
  (
    'fld_TSV020',
    'field',
    'TARGET_VS_MARKET_RESIDUAL_DIRECTION',
    'field_name',
    'target_vs_market_residual_direction',
    NULL,
    'cross_state_features;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model',
    'registry_only',
    'TargetStateVector cross-state group for beta-adjusted target direction/residual behavior relative to broad market context.'
  ),
  (
    'fld_TSV021',
    'field',
    'TARGET_VS_SECTOR_RESIDUAL_DIRECTION',
    'field_name',
    'target_vs_sector_residual_direction',
    NULL,
    'cross_state_features;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model',
    'registry_only',
    'TargetStateVector cross-state group for beta-adjusted target direction/residual behavior relative to admitting sector/industry context.'
  ),
  (
    'fld_TSV022',
    'field',
    'RELATIVE_LIQUIDITY_TRADABILITY_STATE',
    'field_name',
    'relative_liquidity_tradability_state',
    NULL,
    'cross_state_features;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model',
    'registry_only',
    'TargetStateVector cross-state group for target liquidity/tradability and cost relative to accepted sector or universe reference.'
  ),
  (
    'cfg_TSVD001',
    'config',
    'TARGET_STATE_VECTOR_DIRECTION_NEUTRAL_SCORE_FAMILIES',
    'text',
    '3_target_direction_score_<window>;3_target_trend_quality_score_<window>;3_target_path_stability_score_<window>;3_target_noise_score_<window>;3_target_transition_risk_score_<window>;3_target_liquidity_tradability_score;3_context_direction_alignment_score_<window>;3_context_support_quality_score_<window>;3_tradability_score_<window>;3_state_quality_score',
    'trading-model/src/models/model_03_target_state_vector/target_state_vector_contract.md',
    'model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model',
    'registry_only',
    'Reviewed TargetStateVector V1 direction-neutral score families. Direction scores are signed state evidence, not quality, final action, or position sizing.'
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
