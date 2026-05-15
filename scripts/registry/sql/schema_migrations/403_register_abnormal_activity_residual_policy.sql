-- Register residual/provenance boundary for abnormal-activity event evidence.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_EAAR001',
    'config',
    'EVENT_ABNORMAL_ACTIVITY_RESIDUAL_POLICY',
    'text',
    'residual_or_provenance_only;no_duplicate_bar_liquidity_features;incremental_value_required_over_upstream_context_states',
    'trading-model/docs/09_layer_08_event_risk_governor.md',
    'event_risk_governor;source_04_event_overlay;equity_abnormal_activity_event;feature_04_event_overlay;market_context_state;sector_context_state;target_context_state',
    'sync_artifact',
    'Abnormal-activity event evidence may cite bars/liquidity as detector provenance or residual unexplained board/tape disturbance, but must not re-emit model-owned bar/liquidity/target-state features as independent event alpha.'
  ),
  (
    'cfg_EAAB001',
    'config',
    'EVENT_ABNORMAL_ACTIVITY_ALLOWED_USES',
    'text',
    'detector_provenance;residual_unexplained_board_tape_disturbance;discrete_price_action_token;cross_source_abnormal_evidence_not_already_consumed',
    'trading-model/docs/09_layer_08_event_risk_governor.md',
    'event_risk_governor;equity_abnormal_activity_event;price_action;option_abnormal_activity;event_interpretation_v1',
    'sync_artifact',
    'Allowed abnormal-activity uses for event-risk governance after excluding ordinary model-owned market-data features.'
  ),
  (
    'cfg_EAAF001',
    'config',
    'EVENT_ABNORMAL_ACTIVITY_FORBIDDEN_DUPLICATES',
    'text',
    'equity_bar;equity_liquidity_bar;return;volume;spread;liquidity;volatility;gap;vwap_distance;trend;target_state_features',
    'trading-data/docs/94_model_inputs.md',
    'source_04_event_overlay;equity_abnormal_activity_event;event_risk_governor;target_context_state;model_owned_market_data',
    'sync_artifact',
    'Fields and feature families that must not be copied into abnormal-activity event rows as independent event alpha when already consumed by the base model stack.'
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
SET note = 'Default conservative equity abnormal activity detector standard for local detector/provenance evidence generation. It may cite bars/liquidity refs, but must not duplicate ordinary model-owned bar/liquidity features as independent event alpha. Production labels or promoted gates require reviewed historical calibration evidence.',
    updated_at = NOW()
WHERE key = 'EQUITY_ABNORMAL_ACTIVITY_MODEL_STANDARD';

UPDATE trading_registry
SET note = 'Calibration status policy for the equity abnormal activity detector. The default standard is conservative and fixture/development oriented until reviewed historical calibration exists; detector rows are residual/provenance event evidence, not duplicate bar-feature alpha.',
    updated_at = NOW()
WHERE key = 'EQUITY_ABNORMAL_ACTIVITY_CALIBRATION_STATUS';

UPDATE trading_registry
SET note = 'Policy for false-breakout style price-action evidence: represent it as compact event-risk detector/residual evidence with source refs, without duplicating base bar/liquidity features, adding another model layer, or emitting action/execution fields.',
    updated_at = NOW()
WHERE key = 'PRICE_ACTION_EVENT_LAYER_POLICY';
