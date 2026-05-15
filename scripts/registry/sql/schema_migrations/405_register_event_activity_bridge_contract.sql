-- Register event-activity bridge contract connecting events to price/flow/liquidity/options/odds activity.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_EAB001',
    'term',
    'EVENT_ACTIVITY_BRIDGE',
    'text',
    'event_activity_bridge',
    'trading-model/docs/09_layer_08_event_risk_governor.md',
    'event_risk_governor;event_interpretation_v1;event_abnormal_activity_residual_policy;prediction_market;polymarket;source_04_event_overlay',
    'sync_artifact',
    'Contract connecting event evidence to price, liquidity, option, and prediction-market activity. Useful when raw news is difficult to standardize semantically but activity gives stable point-in-time lead/lag or confirmation/divergence evidence.'
  ),
  (
    'cfg_EABR001',
    'config',
    'EVENT_ACTIVITY_BRIDGE_RELATION_TYPES',
    'text',
    'pre_event_precursor;co_event_reaction;post_event_absorption;event_activity_divergence;unresolved_latent_hazard',
    'trading-model/docs/09_layer_08_event_risk_governor.md',
    'event_activity_bridge;event_risk_governor;event_family_training;prediction_market',
    'sync_artifact',
    'Accepted bridge relation types for lead/lag, reaction, absorption, divergence, and unresolved latent hazard evidence.'
  ),
  (
    'cfg_EABE001',
    'config',
    'EVENT_ACTIVITY_BRIDGE_EXPLANATION_STATUS_VALUES',
    'text',
    'explained_by_known_event;partially_explained;unexplained;later_explained;review_required',
    'trading-model/docs/09_layer_08_event_risk_governor.md',
    'event_activity_bridge;point_in_time;event_risk_governor;training_labels',
    'sync_artifact',
    'Accepted explanation-status values. Later explanations create follow-up bridge evidence and must not rewrite the original point-in-time activity record.'
  ),
  (
    'cfg_EABF001',
    'config',
    'EVENT_ACTIVITY_BRIDGE_CORE_FIELDS',
    'text',
    'linked_event_ref;activity_evidence_refs;activity_window;event_window;lead_lag_seconds;residual_activity_score;cross_market_confirmation_score;option_confirmation_score;prediction_market_confirmation_score;explanation_status',
    'trading-model/docs/09_layer_08_event_risk_governor.md',
    'event_activity_bridge;event_interpretation_v1;source_04_event_overlay;prediction_market',
    'sync_artifact',
    'Core field set for the event-activity bridge. Scores are model-owned; source repos preserve refs, windows, and clocks.'
  ),
  (
    'cfg_EABL001',
    'config',
    'EVENT_ACTIVITY_BRIDGE_EVIDENCE_LEGS',
    'text',
    'event_evidence_ref;price_activity_ref;liquidity_activity_ref;option_activity_ref;prediction_market_activity_ref',
    'trading-data/docs/09_layer_08_event_risk_governor.md',
    'event_activity_bridge;trading-data;event_evidence;activity_evidence;prediction_market',
    'sync_artifact',
    'Evidence-leg vocabulary for source-owned bridge refs. Prediction-market activity is included for future Polymarket-style odds/volume/liquidity evidence.'
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
