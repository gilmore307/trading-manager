-- Bulk-align active registry current rows with the completed nine-layer physical renumbering.
-- This intentionally updates current registry values only; historical/applied migration records remain unchanged.

UPDATE trading_registry
SET
  key = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(key,
    'MODEL_04_ALPHA_CONFIDENCE', 'MODEL_05_ALPHA_CONFIDENCE'),
    'MODEL_05_POSITION_PROJECTION', 'MODEL_06_POSITION_PROJECTION'),
    'MODEL_06_UNDERLYING_ACTION', 'MODEL_07_UNDERLYING_ACTION'),
    'MODEL_07_OPTION_EXPRESSION', 'MODEL_08_OPTION_EXPRESSION'),
    'MODEL_08_EVENT_RISK_GOVERNOR', 'MODEL_09_EVENT_RISK_GOVERNOR'),
    'MODEL_08_EVENT_', 'MODEL_09_EVENT_'),
    'SOURCE_08_EVENT_RISK_GOVERNOR', 'SOURCE_09_EVENT_RISK_GOVERNOR'),
    'FEATURE_07_OPTION_EXPRESSION', 'FEATURE_08_OPTION_EXPRESSION'),
    'FEATURE_08_EVENT_RISK_GOVERNOR', 'FEATURE_09_EVENT_RISK_GOVERNOR'),
    'LAYER_07_OPTION', 'LAYER_08_OPTION'),
    'LAYER_EIGHT_EVENT', 'LAYER_NINE_EVENT'),
    'LEGACY_PHYSICAL_MODEL_LAYER_NAME_POLICY', 'CURRENT_PHYSICAL_MODEL_LAYER_NAME_POLICY'),
  payload = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(payload,
    'model_04_alpha_confidence', 'model_05_alpha_confidence'),
    'model_05_position_projection', 'model_06_position_projection'),
    'model_06_underlying_action', 'model_07_underlying_action'),
    'model_07_option_expression', 'model_08_option_expression'),
    'model_08_event_risk_governor', 'model_09_event_risk_governor'),
    'source_08_event_risk_governor', 'source_09_event_risk_governor'),
    'feature_07_option_expression', 'feature_08_option_expression'),
    'feature_08_event_risk_governor', 'feature_09_event_risk_governor'),
    'layer_04_alpha_confidence', 'layer_05_alpha_confidence'),
    'layer_05_position_projection', 'layer_06_position_projection'),
    'layer_06_underlying_action', 'layer_07_underlying_action'),
    'layer_07_option_expression', 'layer_08_option_expression'),
  path = replace(replace(replace(replace(replace(replace(replace(replace(path,
    'model_04_alpha_confidence', 'model_05_alpha_confidence'),
    'model_05_position_projection', 'model_06_position_projection'),
    'model_06_underlying_action', 'model_07_underlying_action'),
    'model_07_option_expression', 'model_08_option_expression'),
    'model_08_event_risk_governor', 'model_09_event_risk_governor'),
    'source_08_event_risk_governor', 'source_09_event_risk_governor'),
    'feature_07_option_expression', 'feature_08_option_expression'),
    'feature_08_event_risk_governor', 'feature_09_event_risk_governor'),
  applies_to = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(applies_to,
    'model_04_alpha_confidence', 'model_05_alpha_confidence'),
    'model_05_position_projection', 'model_06_position_projection'),
    'model_06_underlying_action', 'model_07_underlying_action'),
    'model_07_option_expression', 'model_08_option_expression'),
    'model_08_event_risk_governor', 'model_09_event_risk_governor'),
    'source_08_event_risk_governor', 'source_09_event_risk_governor'),
    'feature_07_option_expression', 'feature_08_option_expression'),
    'feature_08_event_risk_governor', 'feature_09_event_risk_governor'),
    'layer_04_alpha_confidence', 'layer_05_alpha_confidence'),
    'layer_05_position_projection', 'layer_06_position_projection'),
    'layer_06_underlying_action', 'layer_07_underlying_action'),
    'layer_07_option_expression', 'layer_08_option_expression'),
  note = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(note,
    'model_04_alpha_confidence', 'model_05_alpha_confidence'),
    'model_05_position_projection', 'model_06_position_projection'),
    'model_06_underlying_action', 'model_07_underlying_action'),
    'model_07_option_expression', 'model_08_option_expression'),
    'model_08_event_risk_governor', 'model_09_event_risk_governor'),
    'source_08_event_risk_governor', 'source_09_event_risk_governor'),
    'feature_07_option_expression', 'feature_08_option_expression'),
    'feature_08_event_risk_governor', 'feature_09_event_risk_governor'),
    'legacy physical', 'current physical'),
    'legacy model_09', 'current model_09'),
    'legacy model_08', 'current model_09'),
    'legacy source_09', 'current source_09'),
  updated_at = NOW();

UPDATE trading_registry
SET payload = replace(replace(replace(replace(replace(replace(replace(replace(payload,
    '4_alpha_', '5_alpha_'),
    '4_expected_return_', '5_expected_return_'),
    '4_signal_reliability_', '5_signal_reliability_'),
    '4_path_quality_', '5_path_quality_'),
    '4_reversal_risk_', '5_reversal_risk_'),
    '4_drawdown_risk_', '5_drawdown_risk_'),
    '4_base_alpha_', '5_base_alpha_'),
    '4_alpha_tradability_', '5_alpha_tradability_'),
  note = replace(replace(replace(replace(replace(replace(replace(replace(note,
    '4_alpha_', '5_alpha_'),
    '4_expected_return_', '5_expected_return_'),
    '4_signal_reliability_', '5_signal_reliability_'),
    '4_path_quality_', '5_path_quality_'),
    '4_reversal_risk_', '5_reversal_risk_'),
    '4_drawdown_risk_', '5_drawdown_risk_'),
    '4_base_alpha_', '5_base_alpha_'),
    '4_alpha_tradability_', '5_alpha_tradability_'),
  updated_at = NOW();

UPDATE trading_registry
SET payload = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(payload,
    '5_target_position_', '6_target_position_'),
    '5_target_exposure_', '6_target_exposure_'),
    '5_current_position_', '6_current_position_'),
    '5_position_gap_', '6_position_gap_'),
    '5_expected_position_', '6_expected_position_'),
    '5_cost_to_adjust_position_', '6_cost_to_adjust_position_'),
    '5_risk_budget_', '6_risk_budget_'),
    '5_position_state_', '6_position_state_'),
    '5_projection_confidence_', '6_projection_confidence_'),
    '5_resolved_', '6_resolved_'),
  note = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(note,
    '5_target_position_', '6_target_position_'),
    '5_target_exposure_', '6_target_exposure_'),
    '5_current_position_', '6_current_position_'),
    '5_position_gap_', '6_position_gap_'),
    '5_expected_position_', '6_expected_position_'),
    '5_cost_to_adjust_position_', '6_cost_to_adjust_position_'),
    '5_risk_budget_', '6_risk_budget_'),
    '5_position_state_', '6_position_state_'),
    '5_projection_confidence_', '6_projection_confidence_'),
    '5_resolved_', '6_resolved_'),
  updated_at = NOW();

UPDATE trading_registry
SET payload = replace(replace(replace(replace(payload,
    '5_cost_adjustment_reason_codes', '6_cost_adjustment_reason_codes'),
    '5_risk_budget_reason_codes', '6_risk_budget_reason_codes'),
    '5_projection_reason_codes', '6_projection_reason_codes'),
    '5_projection_resolution_confidence_score', '6_projection_resolution_confidence_score'),
  updated_at = NOW();

UPDATE trading_registry
SET payload = replace(replace(replace(replace(payload,
    '6_underlying_', '7_underlying_'),
    '6_resolved_underlying_', '7_resolved_underlying_'),
    '6_resolved_action_', '7_resolved_action_'),
    '6_resolved_trade_', '7_resolved_trade_'),
  note = replace(replace(replace(replace(note,
    '6_underlying_', '7_underlying_'),
    '6_resolved_underlying_', '7_resolved_underlying_'),
    '6_resolved_action_', '7_resolved_action_'),
    '6_resolved_trade_', '7_resolved_trade_'),
  updated_at = NOW();

UPDATE trading_registry
SET payload = replace(replace(payload,
    '7_option_', '8_option_'),
    '7_resolved_', '8_resolved_'),
  note = replace(replace(note,
    '7_option_', '8_option_'),
    '7_resolved_', '8_resolved_'),
  updated_at = NOW();

UPDATE trading_registry
SET payload = replace(payload, '8_event_', '9_event_'),
    note = replace(note, '8_event_', '9_event_'),
    updated_at = NOW();

UPDATE trading_registry
SET applies_to = replace(applies_to, 'legacy_physical_names', 'current_physical_names'),
    note = replace(replace(replace(replace(note,
      'legacy physical-name caveats', 'current physical-name alignment'),
      'Physical receipt ids/model ids remain legacy where noted; ', ''),
      'Physical model_07/7_* names remain legacy. ', 'Current physical model_08/8_* names are active. '),
      'Physical 5_* / model_05 names remain legacy. ', 'Current physical 6_* / model_06 names are active. '),
    updated_at = NOW();

UPDATE trading_registry
SET payload = 'physical_current_numbering_aligned;historical_migrations_and_artifacts_unchanged;compatibility_aliases_only_for_prior_evidence_refs',
    applies_to = 'model_09_event_risk_governor;model_05_alpha_confidence;model_06_position_projection;model_07_underlying_action;model_08_option_expression;source_09_event_risk_governor;feature_09_event_risk_governor;registry_current;openclaw_database',
    note = 'Audit follow-up resolved current-version physical numbering: live/current PostgreSQL table names, stored layer/model values, current registry rows, and current code defaults now follow the accepted nine-layer order. Historical migrations and old artifacts are intentionally not rewritten.',
    updated_at = NOW()
WHERE id = 'cfg_LPNA001';

UPDATE trading_registry
SET payload = 'current_physical_surfaces_aligned_with_nine_layer_order;historical_migrations_and_artifacts_unchanged',
    applies_to = 'layer_04_event_failure_risk;model_05_alpha_confidence;model_06_position_projection;model_07_underlying_action;model_08_option_expression;model_09_event_risk_governor;current_physical_names;model_architecture',
    note = 'After the 2026-05-17 nine-layer reorder and physical renumbering, active script/table/package/stage names use the current Layer 4-9 numbering. Historical/applied migrations and old artifacts remain unchanged for auditability.',
    updated_at = NOW()
WHERE id = 'cfg_LPNM001';
