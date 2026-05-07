-- Register reviewed Layer 5 diagnostic field-family configs that are model-local
-- diagnostics rather than default Layer 6-facing state_vector_value rows.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_ACVBA001',
    'config',
    'ALPHA_CONFIDENCE_BASELINE_ADJUSTMENT_DIAGNOSTIC_SCORE_FAMILIES',
    'text',
    '5_market_adjusted_alpha_score_<horizon>;5_sector_adjusted_alpha_score_<horizon>;5_target_state_lift_score_<horizon>;5_idiosyncratic_alpha_score_<horizon>;5_beta_dependency_score_<horizon>',
    'trading-model/docs/06_layer_05_alpha_confidence.md',
    'alpha_confidence_model;base_alpha_vector;baseline_adjustment_diagnostics;event_adjustment_attribution',
    'registry_only',
    'Reviewed Layer 5 baseline-adjustment diagnostic score-family tokens for separating target-specific alpha from market/sector beta. These are research/audit diagnostics, not default Layer 6-facing state_vector_value rows.'
  ),
  (
    'cfg_ACVEA001',
    'config',
    'ALPHA_CONFIDENCE_EVENT_ADJUSTMENT_DIAGNOSTIC_FIELD_FAMILIES',
    'text',
    '5_event_direction_adjustment_score_<horizon>;5_event_strength_adjustment_score_<horizon>;5_event_confidence_adjustment_score_<horizon>;5_event_risk_adjustment_score_<horizon>;5_event_tradability_adjustment_score_<horizon>;5_event_override_mode_<horizon>;5_event_adjustment_reason_codes_<horizon>',
    'trading-model/docs/06_layer_05_alpha_confidence.md',
    'alpha_confidence_model;event_context_vector;event_adjustment_diagnostics;event_adjustment_attribution',
    'registry_only',
    'Reviewed Layer 5 event-adjustment diagnostic field-family tokens for attributing how EventOverlayModel context changed base alpha. These are research/audit diagnostics and reason-code fields, not default Layer 6-facing state_vector_value rows.'
  )
ON CONFLICT (id) DO UPDATE SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note;
