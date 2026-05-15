-- Register accepted abnormal-activity evidence categories for event-risk governance.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_EAAC001',
    'config',
    'EVENT_ABNORMAL_ACTIVITY_EVIDENCE_CATEGORIES',
    'text',
    'price_action_pattern;residual_market_structure_disturbance;microstructure_liquidity_disruption;option_derivatives_abnormality',
    'trading-model/docs/09_layer_08_event_risk_governor.md',
    'event_abnormal_activity_residual_policy;event_risk_governor;source_04_event_overlay;equity_abnormal_activity_event;price_action;option_abnormal_activity',
    'sync_artifact',
    'Accepted abnormal-activity evidence categories. They are residual/provenance/risk evidence and must not duplicate ordinary model-owned bars, liquidity, trend, or target-state features.'
  ),
  (
    'cfg_EAEX001',
    'config',
    'EVENT_ABNORMAL_ACTIVITY_EXAMPLES',
    'text',
    'price_action_pattern=false_breakout,false_breakdown,liquidity_sweep_high,liquidity_sweep_low,bull_trap,bear_trap;residual_market_structure_disturbance=target_specific_unexplained_board_tape_disturbance_after_context_conditioning;microstructure_liquidity_disruption=spread_widening,depth_disappearance,one_sided_prints,halt_or_pause,anomalous_quote_environment;option_derivatives_abnormality=iv_shock,skew_or_term_structure_shock,unusual_option_volume,call_put_imbalance,sweep_or_block_evidence,oi_change,option_liquidity_disruption',
    'trading-data/docs/94_model_inputs.md',
    'event_abnormal_activity_residual_policy;event_family_training;golden_tests;event_risk_governor',
    'sync_artifact',
    'Concrete examples for abnormal-activity residual/provenance event evidence. Examples are not buy/sell/hold signals and do not prove production calibration.'
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

UPDATE trading_registry
SET payload = 'detector_provenance;residual_unexplained_board_tape_disturbance;discrete_price_action_token;cross_source_abnormal_evidence_not_already_consumed;microstructure_liquidity_disruption;option_derivatives_abnormality',
    note = 'Allowed abnormal-activity uses for event-risk governance after excluding ordinary model-owned market-data features. Use category values from EVENT_ABNORMAL_ACTIVITY_EVIDENCE_CATEGORIES for implementation-facing classification.',
    updated_at = NOW()
WHERE key = 'EVENT_ABNORMAL_ACTIVITY_ALLOWED_USES';
