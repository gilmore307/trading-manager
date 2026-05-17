-- Register narrow startup abnormality scope for Layer 9 activity bridge evidence.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_EABAS001',
    'config',
    'EVENT_ACTIVITY_BRIDGE_ABNORMALITY_STARTUP_SCOPE',
    'text',
    'price_action_pattern=false_breakout,false_breakdown,liquidity_sweep_high,liquidity_sweep_low,bull_trap,bear_trap;residual_market_structure_disturbance=target_specific_board_tape_disturbance_after_upstream_conditioning;microstructure_liquidity_disruption=spread_widening,depth_disappearance,quote_quality_breakdown,one_sided_prints,halt_or_pause,anomalous_quote_environment;option_derivatives_abnormality=iv_shock,skew_or_term_structure_shock,unusual_option_volume,call_put_imbalance,sweep_or_block_evidence,oi_change,option_liquidity_disruption',
    'trading-model/docs/10_layer_09_event_risk_governor.md',
    'event_activity_bridge;event_risk_governor;abnormal_activity;startup_scope;source_09_event_risk_governor',
    'sync_artifact',
    'Narrow startup abnormality scope for Layer 9 activity bridge evidence. These are compact point-in-time detector refs only, not standalone alpha or duplicated upstream model features.'
  ),
  (
    'cfg_EABEX001',
    'config',
    'EVENT_ACTIVITY_BRIDGE_ABNORMALITY_EXCLUDED_STARTUP_SCOPE',
    'text',
    'raw_return_zscore_alone;raw_volume_zscore_alone;raw_spread_or_liquidity_zscore_alone;ordinary_equity_bar_fields;ordinary_equity_liquidity_bar_fields;target_state_features;option_expression_inputs;layer_08_guidance_payload_fields;strategy_or_base_stack_failure_labels;post_event_realized_labels;uncalibrated_detector_thresholds_without_review',
    'trading-manager/docs/81_decision.md#D211',
    'event_activity_bridge;event_risk_governor;abnormal_activity;startup_scope;non_overlap_gate',
    'sync_artifact',
    'Excluded startup scope for activity bridge abnormality evidence. Excluded items may remain audit/provenance refs but must not become incremental event evidence without reviewed residual/non-overlap proof.'
  ),
  (
    'cfg_EABNO001',
    'config',
    'EVENT_ACTIVITY_BRIDGE_NON_OVERLAP_STATUSES',
    'text',
    'not_in_upstream_features;residual_after_upstream_conditioning;review_required_overlap_unknown',
    'trading-manager/docs/81_decision.md#D210',
    'event_activity_bridge;event_risk_governor;abnormal_activity;non_overlap_gate',
    'sync_artifact',
    'Accepted upstream non-overlap statuses for activity bridge evidence. Only not_in_upstream_features and residual_after_upstream_conditioning may support scoring/intervention evidence.'
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
