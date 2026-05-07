-- Align Layer 5 AlphaConfidenceModel registry rows with the accepted base-vs-adjusted contract.
-- Final adjusted alpha_confidence_vector remains the Layer 6-facing output. Base/unadjusted
-- Layer 1/2/3 alpha fields are diagnostics for audit/research/event-attribution only.

UPDATE trading_registry
SET
  path = 'trading-model/docs/06_layer_05_alpha_confidence.md',
  applies_to = 'trading-model;market_context_state;sector_context_state;target_context_state;event_context_vector;model_05_alpha_confidence;alpha_confidence_vector',
  note = 'Accepted canonical Layer 5 model id. AlphaConfidenceModel builds base/unadjusted alpha diagnostics from the Layer 1/2/3 state stack, uses event_context_vector plus quality/calibration/path-risk controls as a correction layer, and emits the final adjusted alpha_confidence_vector; it is separate from Layer 3 state evidence, Layer 4 event context, and Layer 6 trading projection.',
  updated_at = NOW()
WHERE kind = 'term'
  AND key = 'ALPHA_CONFIDENCE_MODEL';

UPDATE trading_registry
SET
  path = 'trading-model/docs/06_layer_05_alpha_confidence.md',
  applies_to = 'trading-model;alpha_confidence_model;market_context_state;sector_context_state;target_context_state;event_context_vector;alpha_confidence_vector',
  note = 'Accepted Layer 5 AlphaConfidenceModel model-output surface name for future promoted final adjusted alpha_confidence_vector outputs. Base/unadjusted alpha fields are diagnostics, not the default Layer 6-facing surface.',
  updated_at = NOW()
WHERE kind = 'term'
  AND key = 'MODEL_05_ALPHA_CONFIDENCE';

UPDATE trading_registry
SET
  path = 'trading-model/docs/06_layer_05_alpha_confidence.md',
  applies_to = 'trading-model;alpha_confidence_model;model_05_alpha_confidence;market_context_state;sector_context_state;target_context_state;event_context_vector',
  note = 'Layer 5 AlphaConfidenceModel final adjusted output vector with horizon-aware alpha direction, strength, expected residual return, confidence, reliability, path quality, reversal risk, drawdown risk, and alpha-level tradability; not a final action, target exposure, position-sizing, or option-expression instruction.',
  updated_at = NOW()
WHERE kind = 'term'
  AND key = 'ALPHA_CONFIDENCE_VECTOR';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('cfg_ACVH001', 'config', 'ALPHA_CONFIDENCE_VECTOR_HORIZONS', 'text', '5min;15min;60min;390min', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;alpha_confidence_model;model_05_alpha_confidence', 'registry_only', 'Accepted AlphaConfidenceModel V1 prediction horizons. 390min means one regular US equity session-equivalent horizon measured in tradable minutes; label builders must document same-session vs next-session-close resolution and use purge/embargo controls.'),
  ('cfg_ACVS001', 'config', 'ALPHA_CONFIDENCE_VECTOR_SCORE_FAMILIES', 'text', '5_alpha_direction_score_<horizon>;5_alpha_strength_score_<horizon>;5_expected_return_score_<horizon>;5_alpha_confidence_score_<horizon>;5_signal_reliability_score_<horizon>;5_path_quality_score_<horizon>;5_reversal_risk_score_<horizon>;5_drawdown_risk_score_<horizon>;5_alpha_tradability_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;alpha_confidence_model;model_05_alpha_confidence;state_vector_value', 'registry_only', 'Accepted Layer 5 AlphaConfidenceModel V1 final adjusted scalar score-family tokens. These 9 families separate alpha direction, strength, expected residual return, confidence, reliability, path quality, reversal risk, drawdown risk, and alpha-level tradability.'),
  ('cfg_ACVBD001', 'config', 'ALPHA_CONFIDENCE_BASE_DIAGNOSTIC_SCORE_FAMILIES', 'text', '5_base_alpha_direction_score_<horizon>;5_base_alpha_strength_score_<horizon>;5_base_expected_return_score_<horizon>;5_base_path_quality_score_<horizon>;5_base_reversal_risk_score_<horizon>;5_base_drawdown_risk_score_<horizon>;5_base_alpha_tradability_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_model;base_alpha_vector;diagnostics;event_adjustment_attribution', 'registry_only', 'Reviewed Layer 5 base/unadjusted Layer 1/2/3 alpha diagnostic score-family tokens. These are research/audit/event-attribution diagnostics, not default Layer 6-facing state_vector_value rows.'),
  ('cfg_ACVTP001', 'config', 'ALPHA_CONFIDENCE_VECTOR_OUTPUT_TIER_POLICY', 'text', 'base_unadjusted_diagnostic_only;final_adjusted_layer_6_facing', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_model;alpha_confidence_vector;base_alpha_vector;model_06_trading_projection', 'registry_only', 'Layer 5 output-tier policy: base/unadjusted alpha from Layer 1/2/3 is diagnostic-only, while final adjusted alpha_confidence_vector is the default Layer 6-facing output.'),
  ('fld_ACMV1001', 'state_vector_value', 'ALPHA_DIRECTION_SCORE_BY_HORIZON', 'field_name', '5_alpha_direction_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;model_05_alpha_confidence;alpha_confidence_model;market_context_state;sector_context_state;target_context_state;event_context_vector;model_evaluation;promotion_evidence', 'registry_only', 'Layer 5 AlphaConfidence signed final adjusted score family for horizon-aware alpha direction; positive is long alpha, negative is short alpha, and this is not a buy/sell/hold action.'),
  ('fld_ACMV1002', 'state_vector_value', 'ALPHA_STRENGTH_SCORE_BY_HORIZON', 'field_name', '5_alpha_strength_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;model_05_alpha_confidence;alpha_confidence_model;model_evaluation;promotion_evidence', 'registry_only', 'Layer 5 AlphaConfidence final adjusted score family for absolute alpha strength by horizon regardless of long/short sign.'),
  ('fld_ACMV1003', 'state_vector_value', 'ALPHA_EXPECTED_RETURN_SCORE_BY_HORIZON', 'field_name', '5_expected_return_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;model_05_alpha_confidence;alpha_confidence_model;model_evaluation;promotion_evidence', 'registry_only', 'Layer 5 AlphaConfidence signed final adjusted score family for standardized residual expected return by horizon after market/sector baseline adjustment and before trading projection.'),
  ('fld_ACMV1004', 'state_vector_value', 'ALPHA_CONFIDENCE_SCORE_BY_HORIZON', 'field_name', '5_alpha_confidence_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;model_05_alpha_confidence;alpha_confidence_model;model_evaluation;promotion_evidence', 'registry_only', 'Layer 5 AlphaConfidence final adjusted score family for model confidence in the alpha judgment by horizon; confidence is not alpha strength and not a trade instruction.'),
  ('fld_ACMV1005', 'state_vector_value', 'SIGNAL_RELIABILITY_SCORE_BY_HORIZON', 'field_name', '5_signal_reliability_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;model_05_alpha_confidence;alpha_confidence_model;model_evaluation;promotion_evidence', 'registry_only', 'Layer 5 AlphaConfidence final adjusted score family for historical out-of-sample reliability of similar signals by horizon.'),
  ('fld_ACMV1006', 'state_vector_value', 'PATH_QUALITY_SCORE_BY_HORIZON', 'field_name', '5_path_quality_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;model_05_alpha_confidence;alpha_confidence_model;model_evaluation;promotion_evidence', 'registry_only', 'Layer 5 AlphaConfidence high-is-good final adjusted score family for expected forward path quality/tradability by horizon.'),
  ('fld_ACMV1007', 'state_vector_value', 'REVERSAL_RISK_SCORE_BY_HORIZON', 'field_name', '5_reversal_risk_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;model_05_alpha_confidence;alpha_confidence_model;model_evaluation;promotion_evidence', 'registry_only', 'Layer 5 AlphaConfidence high-is-bad final adjusted score family for risk that the alpha direction is interrupted or reversed by horizon.'),
  ('fld_ACMV1008', 'state_vector_value', 'DRAWDOWN_RISK_SCORE_BY_HORIZON', 'field_name', '5_drawdown_risk_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;model_05_alpha_confidence;alpha_confidence_model;model_evaluation;promotion_evidence', 'registry_only', 'Layer 5 AlphaConfidence high-is-bad final adjusted score family for adverse excursion, MAE, or drawdown risk by horizon.'),
  ('fld_ACMV1009', 'state_vector_value', 'ALPHA_TRADABILITY_SCORE_BY_HORIZON', 'field_name', '5_alpha_tradability_score_<horizon>', 'trading-model/docs/06_layer_05_alpha_confidence.md', 'alpha_confidence_vector;model_05_alpha_confidence;alpha_confidence_model;model_06_trading_projection;model_evaluation;promotion_evidence', 'registry_only', 'Layer 5 AlphaConfidence final adjusted alpha-level suitability score for Layer 6 trading projection by horizon; this is not a trading signal, target exposure, or position size.')
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

DELETE FROM trading_registry
WHERE id IN ('fld_ACMV1010', 'fld_ACMV1011')
   OR (kind = 'state_vector_value' AND key IN (
      'ALPHA_EVENT_ADJUSTMENT_SCORE_BY_HORIZON',
      'ALPHA_CALIBRATION_QUALITY_SCORE_BY_HORIZON'
   ));
