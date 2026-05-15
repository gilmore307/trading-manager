-- Register activity-price relationship proof gate before event-activity bridge model-layer promotion.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_APRG001',
    'config',
    'ACTIVITY_PRICE_RELATIONSHIP_PROOF_GATE',
    'text',
    'required_before_event_activity_bridge_model_promotion',
    'trading-model/docs/09_layer_08_event_risk_governor.md',
    'event_activity_bridge;event_risk_governor;abnormal_activity;model_promotion;training_labels',
    'sync_artifact',
    'Abnormal activity must prove stable point-in-time forward price/path relationship before becoming a separate model layer or risk-intervention input.'
  ),
  (
    'cfg_APRL001',
    'config',
    'ACTIVITY_PRICE_RELATIONSHIP_PROOF_LEVELS',
    'text',
    'contemporaneous_association;forward_price_path_relationship;incremental_residual_value;cross_market_confirmation_value;out_of_sample_stability',
    'trading-model/docs/09_layer_08_event_risk_governor.md',
    'event_activity_bridge;model_evaluation;model_promotion;abnormal_activity',
    'sync_artifact',
    'Required proof levels. Current-window association alone is insufficient; forward and incremental residual evidence are required.'
  ),
  (
    'cfg_APRF001',
    'config',
    'ACTIVITY_PRICE_RELATIONSHIP_FORWARD_LABEL_FAMILIES',
    'text',
    'forward_return;forward_drawdown;forward_reversal;forward_volatility_expansion;forward_gap_or_jump;path_asymmetry',
    'trading-model/docs/09_layer_08_event_risk_governor.md',
    'event_activity_bridge;training_labels;model_evaluation;abnormal_activity',
    'sync_artifact',
    'Forward label families used to test whether abnormal activity has a stable relationship to subsequent price/path outcomes.'
  ),
  (
    'cfg_APRH001',
    'config',
    'ACTIVITY_PRICE_RELATIONSHIP_TEST_HORIZONS',
    'text',
    '5m;30m;1h;1d;5d;20d',
    'trading-model/docs/09_layer_08_event_risk_governor.md',
    'event_activity_bridge;training_labels;model_evaluation;abnormal_activity',
    'sync_artifact',
    'Initial short and event-relevant horizons for abnormal-activity to forward-price/path relationship tests.'
  ),
  (
    'cfg_APRC001',
    'config',
    'ACTIVITY_PRICE_RELATIONSHIP_REQUIRED_CONTROLS',
    'text',
    'market_context;sector_context;peer_context;target_state;ordinary_bar_volume_liquidity_volatility_features;scheduled_event_calendar_shells;time_of_day_day_of_week_month_effects;broad_market_liquidity_volatility_regime',
    'trading-model/docs/09_layer_08_event_risk_governor.md',
    'event_activity_bridge;model_evaluation;leakage_control;abnormal_activity',
    'sync_artifact',
    'Controls required before abnormal activity can claim incremental residual value over existing market-data and model-stack information.'
  ),
  (
    'cfg_APRW001',
    'config',
    'ACTIVITY_PRICE_RELATIONSHIP_WINDOW_SEPARATION_POLICY',
    'text',
    'activity_detection_window;event_availability_window;forward_label_window',
    'trading-data/docs/09_layer_08_event_risk_governor.md',
    'event_activity_bridge;trading-data;training_labels;leakage_control',
    'sync_artifact',
    'Detector inputs, event availability, and forward labels must use separate windows so price-derived abnormality is not validated against the same interval that created it.'
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
