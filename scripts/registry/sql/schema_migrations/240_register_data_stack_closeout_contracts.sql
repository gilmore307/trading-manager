-- Register trading-data closeout/readiness contracts after data-source/model-input design closeout.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_DSC001',
    'config',
    'TRADING_DATA_STACK_CLOSEOUT_STATUS',
    'text',
    'data_source_model_input_design_closed;production_hardening_pending;durable_manager_storage_contracts_pending;no_unattended_production_orchestration_approval',
    'trading-data/docs/95_data_stack_closeout.md',
    'trading-data;data_feed;data_source;data_feature;model_inputs;production_hardening',
    'registry_only',
    'Accepted trading-data closeout status for the current feed/source/feature model-input design phase. It does not approve unattended production orchestration or final durable storage contracts.'
  ),
  (
    'cfg_DSC002',
    'config',
    'ETF_HOLDINGS_AVAILABLE_TIME_POLICY',
    'text',
    'explicit_available_time_wins;default_next_regular_us_session_open_after_as_of_date;skip_weekends;same_day_requires_source_evidence',
    'trading-data/src/data_source/source_02_target_candidate_holdings/README.md',
    'source_02_target_candidate_holdings;stock_etf_exposure;anonymous_target_candidate_builder;available_time;point_in_time',
    'registry_only',
    'Conservative point-in-time availability policy for ETF holdings candidate-preparation rows. Without explicit availability evidence, holdings become model-visible at the next regular US session open after as_of_date.'
  ),
  (
    'cfg_DSC003',
    'config',
    'EQUITY_ABNORMAL_ACTIVITY_MODEL_STANDARD',
    'text',
    'equity_abnormal_activity_conservative_v1',
    'trading-data/src/data_source/source_04_event_overlay/equity_abnormal_activity/config.json',
    'equity_abnormal_activity_event;source_04_event_overlay;event_overlay_model;model_standard;production_calibration',
    'registry_only',
    'Default conservative equity abnormal activity detector standard for local evidence generation. Production labels or promoted gates require reviewed historical calibration evidence before relying on this standard as production-calibrated.'
  ),
  (
    'cfg_DSC004',
    'config',
    'EQUITY_ABNORMAL_ACTIVITY_CALIBRATION_STATUS',
    'text',
    'conservative_fixture_default_not_production_calibrated;historical_calibration_required_before_training_label_or_promotion_gate_use',
    'trading-data/docs/95_data_stack_closeout.md',
    'equity_abnormal_activity_event;source_04_event_overlay;event_overlay_model;training_labels;promotion_gates',
    'registry_only',
    'Calibration status policy for the equity abnormal activity detector. The default standard is conservative and fixture/development oriented until a reviewed historical calibration report exists.'
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
  updated_at = NOW();
