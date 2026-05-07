-- Register accepted Layer 5 AlphaConfidenceModel alpha-confidence vector score families.
-- These are reviewed core scalar state_vector_value tokens for calibrated confidence,
-- expected value, risk, uncertainty, context support, event adjustment, and calibration
-- quality. They are not trading-projection, option-expression, position-sizing, or
-- final-action outputs.

UPDATE trading_registry
SET
  path = 'trading-model/docs/06_layer_05_alpha_confidence.md',
  applies_to = 'trading-model;target_context_state;event_context_vector;model_05_alpha_confidence;alpha_confidence_vector',
  note = 'Accepted canonical Layer 5 model id. AlphaConfidenceModel maps target_context_state plus event_context_vector to calibrated long/short alpha confidence, expected return/value, risk, uncertainty, context support, event adjustment, and calibration quality; it is separate from Layer 3 direction evidence, Layer 4 event context, and Layer 6 trading projection.',
  updated_at = NOW()
WHERE kind = 'term'
  AND key = 'ALPHA_CONFIDENCE_MODEL';

UPDATE trading_registry
SET
  path = 'trading-model/docs/06_layer_05_alpha_confidence.md',
  applies_to = 'trading-model;alpha_confidence_model;target_context_state;event_context_vector;alpha_confidence_vector',
  note = 'Accepted Layer 5 AlphaConfidenceModel model-output surface name for future promoted alpha_confidence_vector outputs.',
  updated_at = NOW()
WHERE kind = 'term'
  AND key = 'MODEL_05_ALPHA_CONFIDENCE';

UPDATE trading_registry
SET
  path = 'trading-model/docs/06_layer_05_alpha_confidence.md',
  applies_to = 'trading-model;alpha_confidence_model;model_05_alpha_confidence;target_context_state;event_context_vector',
  note = 'Layer 5 AlphaConfidenceModel output vector for calibrated long/short confidence, expected return/value, risk, uncertainty, context support, event adjustment, and calibration quality; not a final action, target exposure, position-sizing, or option-expression instruction.',
  updated_at = NOW()
WHERE kind = 'term'
  AND key = 'ALPHA_CONFIDENCE_VECTOR';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('cfg_ACVH001', 'config', 'ALPHA_CONFIDENCE_VECTOR_HORIZONS', 'text', '5min;15min;60min;390min', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;alpha_confidence_model;model_05_alpha_confidence', 'registry_only', 'Accepted AlphaConfidenceModel V1 prediction horizons. Horizons are alpha-confidence horizons, not trade-action variants and not option-expiration choices.'),
  ('cfg_ACVS001', 'config', 'ALPHA_CONFIDENCE_VECTOR_SCORE_FAMILIES', 'text', '5_alpha_direction_confidence_score_<horizon>;5_alpha_direction_strength_score_<horizon>;5_alpha_expected_return_score_<horizon>;5_alpha_expected_value_score_<horizon>;5_alpha_downside_risk_score_<horizon>;5_alpha_tail_risk_score_<horizon>;5_alpha_path_stability_score_<horizon>;5_alpha_uncertainty_score_<horizon>;5_alpha_context_support_score_<horizon>;5_alpha_event_adjustment_score_<horizon>;5_alpha_calibration_quality_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;alpha_confidence_model;model_05_alpha_confidence;state_vector_value', 'registry_only', 'Accepted Layer 5 AlphaConfidenceModel V1 scalar score-family tokens. These families separate calibrated direction confidence, strength, expected return/value, downside/tail/path risk, uncertainty, context support, event adjustment, and calibration quality.'),
  ('fld_ACMV1001', 'state_vector_value', 'ALPHA_DIRECTION_CONFIDENCE_SCORE_BY_HORIZON', 'field_name', '5_alpha_direction_confidence_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;model_05_alpha_confidence;alpha_confidence_model;target_context_state;event_context_vector;model_evaluation;promotion_evidence', 'registry_only', 'Layer 5 AlphaConfidence signed score family for calibrated long/short alpha confidence by horizon; this is not a buy/sell/hold action.'),
  ('fld_ACMV1002', 'state_vector_value', 'ALPHA_DIRECTION_STRENGTH_SCORE_BY_HORIZON', 'field_name', '5_alpha_direction_strength_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;model_05_alpha_confidence;alpha_confidence_model;model_evaluation;promotion_evidence', 'registry_only', 'Layer 5 AlphaConfidence score family for absolute confidence strength by horizon regardless of long/short sign.'),
  ('fld_ACMV1003', 'state_vector_value', 'ALPHA_EXPECTED_RETURN_SCORE_BY_HORIZON', 'field_name', '5_alpha_expected_return_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;model_05_alpha_confidence;alpha_confidence_model;model_evaluation;promotion_evidence', 'registry_only', 'Layer 5 AlphaConfidence signed score family for normalized forward return expectation by horizon before trading projection.'),
  ('fld_ACMV1004', 'state_vector_value', 'ALPHA_EXPECTED_VALUE_SCORE_BY_HORIZON', 'field_name', '5_alpha_expected_value_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;model_05_alpha_confidence;alpha_confidence_model;model_evaluation;promotion_evidence', 'registry_only', 'Layer 5 AlphaConfidence signed score family for risk/uncertainty-adjusted alpha expected value by horizon before account-specific costs, expression, or sizing.'),
  ('fld_ACMV1005', 'state_vector_value', 'ALPHA_DOWNSIDE_RISK_SCORE_BY_HORIZON', 'field_name', '5_alpha_downside_risk_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;model_05_alpha_confidence;alpha_confidence_model;model_evaluation;promotion_evidence', 'registry_only', 'Layer 5 AlphaConfidence high-is-bad score family for adverse path or loss risk by horizon.'),
  ('fld_ACMV1006', 'state_vector_value', 'ALPHA_TAIL_RISK_SCORE_BY_HORIZON', 'field_name', '5_alpha_tail_risk_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;model_05_alpha_confidence;alpha_confidence_model;model_evaluation;promotion_evidence', 'registry_only', 'Layer 5 AlphaConfidence high-is-bad score family for extreme adverse outcome or tail-loss risk by horizon.'),
  ('fld_ACMV1007', 'state_vector_value', 'ALPHA_PATH_STABILITY_SCORE_BY_HORIZON', 'field_name', '5_alpha_path_stability_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;model_05_alpha_confidence;alpha_confidence_model;model_evaluation;promotion_evidence', 'registry_only', 'Layer 5 AlphaConfidence high-is-good score family for expected forward path smoothness/tradability by horizon.'),
  ('fld_ACMV1008', 'state_vector_value', 'ALPHA_UNCERTAINTY_SCORE_BY_HORIZON', 'field_name', '5_alpha_uncertainty_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;model_05_alpha_confidence;alpha_confidence_model;model_evaluation;promotion_evidence', 'registry_only', 'Layer 5 AlphaConfidence high-is-bad score family for model confidence unreliability by horizon.'),
  ('fld_ACMV1009', 'state_vector_value', 'ALPHA_CONTEXT_SUPPORT_SCORE_BY_HORIZON', 'field_name', '5_alpha_context_support_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;model_05_alpha_confidence;alpha_confidence_model;target_context_state;event_context_vector;model_evaluation;promotion_evidence', 'registry_only', 'Layer 5 AlphaConfidence high-is-good score family for coherent market/sector/target/event support by horizon.'),
  ('fld_ACMV1010', 'state_vector_value', 'ALPHA_EVENT_ADJUSTMENT_SCORE_BY_HORIZON', 'field_name', '5_alpha_event_adjustment_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;model_05_alpha_confidence;alpha_confidence_model;event_context_vector;model_evaluation;promotion_evidence', 'registry_only', 'Layer 5 AlphaConfidence signed score family for event-driven confidence adjustment by horizon relative to no-event baseline.'),
  ('fld_ACMV1011', 'state_vector_value', 'ALPHA_CALIBRATION_QUALITY_SCORE_BY_HORIZON', 'field_name', '5_alpha_calibration_quality_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;model_05_alpha_confidence;alpha_confidence_model;model_evaluation;promotion_evidence', 'registry_only', 'Layer 5 AlphaConfidence high-is-good score family for reliability/calibration quality by horizon.')
ON CONFLICT (id) DO UPDATE SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note;
