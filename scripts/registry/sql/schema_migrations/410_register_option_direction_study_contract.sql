-- Register option-activity directional study contract.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_OPDIR001',
    'config',
    'OPTION_ACTIVITY_DIRECTION_REQUIRED_EVIDENCE_FIELDS',
    'text',
    'option_right;trade_side_or_aggressor_side;ask_touch_ratio;bid_touch_ratio;sweep_or_block_context;trade_size;trade_notional;window_volume;open_interest_change;opening_or_closing_context;iv_change;skew_direction;term_structure_direction;direction_confidence',
    'trading-model/docs/99_activity_price_relationship_study.md',
    'option_activity;activity_direction;event_activity_bridge;activity_price_relationship_study',
    'sync_artifact',
    'Minimum evidence fields for option-activity direction studies. Raw call/put volume alone is not directional proof.'
  ),
  (
    'cfg_OPDIR002',
    'config',
    'OPTION_ACTIVITY_DIRECTION_HYPOTHESES',
    'text',
    'ask_side_call_activity=bullish_activity;ask_side_put_activity=bearish_activity;bid_side_call_activity=bearish_activity_or_call_selling;bid_side_put_activity=bullish_activity_or_put_selling;call_put_ask_side_imbalance_positive=bullish_activity;call_put_ask_side_imbalance_negative=bearish_activity;iv_expansion_without_side=unknown_direction_activity;call_skew_richening=bullish_activity_or_upside_demand;put_skew_richening=bearish_activity_or_downside_demand',
    'trading-model/docs/99_activity_price_relationship_study.md',
    'option_activity;directional_classification;event_activity_bridge;training_labels',
    'sync_artifact',
    'Initial option-direction hypotheses. They must be evaluated by signed directional forward labels, not assumed as facts.'
  ),
  (
    'cfg_OPDIR003',
    'config',
    'OPTION_ACTIVITY_DIRECTION_REQUIRED_COMPARISONS',
    'text',
    'call_ask_side_events_vs_non_event_option_windows;put_ask_side_events_vs_non_event_option_windows;call_put_ask_side_imbalance_buckets;iv_only_expansion_without_side_evidence;sweep_block_events_vs_ordinary_prints;opening_volume_vs_ambiguous_or_closing_volume;option_direction_confirmed_by_underlying_vs_option_underlying_divergence',
    'trading-model/docs/99_activity_price_relationship_study.md',
    'option_activity;activity_price_relationship_study;model_evaluation',
    'sync_artifact',
    'Required comparisons for the option-activity direction study.'
  ),
  (
    'cfg_OPDIR004',
    'config',
    'OPTION_ACTIVITY_DIRECTION_FORWARD_LABELS',
    'text',
    'underlying_signed_directional_forward_return;underlying_absolute_forward_return;option_contract_signed_forward_return;option_contract_absolute_forward_return;implied_vol_forward_change;skew_forward_change',
    'trading-model/docs/99_activity_price_relationship_study.md',
    'option_activity;training_labels;activity_direction;event_activity_bridge',
    'sync_artifact',
    'Forward labels for testing whether option activity has directional value for the underlying and/or the option contract itself.'
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
