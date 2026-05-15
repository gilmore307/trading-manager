-- Register directional abnormal-activity proof labels separate from direction-neutral path expansion.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_APDIR001',
    'config',
    'ACTIVITY_DIRECTION_CLASSES',
    'text',
    'bullish_activity;bearish_activity;neutral_activity;mixed_or_conflicting_activity;unknown_direction_activity',
    'trading-model/docs/99_activity_price_relationship_study.md',
    'activity_price_relationship_study;abnormal_activity;event_activity_bridge;option_activity',
    'sync_artifact',
    'Direction classes for abnormal activity. Direction must come from point-in-time evidence, not future labels.'
  ),
  (
    'cfg_APDIR002',
    'config',
    'ACTIVITY_DIRECTIONAL_PROOF_METRICS',
    'text',
    'activity_direction_bias_score;activity_direction_confidence_score;signed_directional_forward_return;directional_hit_rate;opposite_direction_failure_rate;mixed_direction_conflict_score',
    'trading-model/docs/99_activity_price_relationship_study.md',
    'activity_price_relationship_study;directional_classification;training_labels;event_activity_bridge',
    'sync_artifact',
    'Metrics for the second activity-price gate: whether point-in-time activity orientation predicts signed forward direction.'
  ),
  (
    'cfg_APDIR003',
    'config',
    'OPTION_ACTIVITY_DIRECTION_EVIDENCE_FIELDS',
    'text',
    'option_right;trade_side_or_aggressor_side;call_put_imbalance;sweep_or_block_context;open_interest_change;opening_or_closing_context;iv_skew_direction;direction_confidence',
    'trading-data/docs/81_decision.md',
    'option_activity;activity_direction;event_activity_bridge;trading-data',
    'sync_artifact',
    'Option direction requires call/put side and aggressor/opening context when available. Raw call or put volume alone is not enough to assert direction.'
  ),
  (
    'cfg_APDIR004',
    'config',
    'ACTIVITY_DIRECTION_EXAMPLE_MAPPING',
    'text',
    'call_buying_surge=bullish_activity;call_sweep_ask_side=bullish_activity;put_buying_surge=bearish_activity;put_sweep_ask_side=bearish_activity;positive_residual_return=bullish_activity;negative_residual_return=bearish_activity;high_liquidity_sweep_reversal=bearish_activity;low_liquidity_sweep_reversal=bullish_activity;iv_expansion_without_side=unknown_direction_activity;mixed_call_put_flow=mixed_or_conflicting_activity',
    'trading-model/docs/99_activity_price_relationship_study.md',
    'activity_price_relationship_study;abnormal_activity;option_activity;directional_classification',
    'sync_artifact',
    'Initial directional evidence mapping for testing. Mapping is a hypothesis and must be evaluated by signed directional forward labels.'
  )
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();
