-- Align active registry rows with current conceptual layer numbering after the
-- live/current PostgreSQL table migration. Historical migration files remain unchanged.

UPDATE trading_registry
SET key = replace(replace(replace(replace(replace(replace(replace(replace(key,
        'SOURCE_04_EVENT_OVERLAY', 'SOURCE_08_EVENT_RISK_GOVERNOR'),
        'FEATURE_04_EVENT_OVERLAY', 'FEATURE_08_EVENT_RISK_GOVERNOR'),
        'FEATURE_08_OPTION_EXPRESSION', 'FEATURE_07_OPTION_EXPRESSION'),
        'MODEL_05_ALPHA_CONFIDENCE', 'MODEL_04_ALPHA_CONFIDENCE'),
        'MODEL_06_POSITION_PROJECTION', 'MODEL_05_POSITION_PROJECTION'),
        'MODEL_07_UNDERLYING_ACTION', 'MODEL_06_UNDERLYING_ACTION'),
        'MODEL_08_OPTION_EXPRESSION', 'MODEL_07_OPTION_EXPRESSION'),
        'LAYER_08_OPTION_EXPRESSION', 'LAYER_07_OPTION_EXPRESSION'),
    payload = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(payload,
        'source_04_event_overlay', 'source_08_event_risk_governor'),
        'feature_04_event_overlay', 'feature_08_event_risk_governor'),
        'feature_08_option_expression', 'feature_07_option_expression'),
        'model_05_alpha_confidence', 'model_04_alpha_confidence'),
        'model_06_position_projection', 'model_05_position_projection'),
        'model_07_underlying_action', 'model_06_underlying_action'),
        'model_08_option_expression', 'model_07_option_expression'),
        'layer_04_event_overlay', 'layer_08_event_risk_governor'),
        'layer_05_alpha_confidence', 'layer_04_alpha_confidence'),
        'layer_06_position_projection', 'layer_05_position_projection'),
        'layer_07_underlying_action', 'layer_06_underlying_action'),
        'layer_08_option_expression', 'layer_07_option_expression'),
        '4_event_', '8_event_'),
        '8_option_', '7_option_'),
    path = replace(replace(replace(replace(replace(replace(replace(path,
        'source_04_event_overlay', 'source_08_event_risk_governor'),
        'feature_04_event_overlay', 'feature_08_event_risk_governor'),
        'feature_08_option_expression', 'feature_07_option_expression'),
        'model_05_alpha_confidence', 'model_04_alpha_confidence'),
        'model_06_position_projection', 'model_05_position_projection'),
        'model_07_underlying_action', 'model_06_underlying_action'),
        'model_08_option_expression', 'model_07_option_expression'),
    applies_to = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(applies_to,
        'source_04_event_overlay', 'source_08_event_risk_governor'),
        'feature_04_event_overlay', 'feature_08_event_risk_governor'),
        'feature_08_option_expression', 'feature_07_option_expression'),
        'model_05_alpha_confidence', 'model_04_alpha_confidence'),
        'model_06_position_projection', 'model_05_position_projection'),
        'model_07_underlying_action', 'model_06_underlying_action'),
        'model_08_option_expression', 'model_07_option_expression'),
        'layer_04_event_overlay', 'layer_08_event_risk_governor'),
        'layer_05_alpha_confidence', 'layer_04_alpha_confidence'),
        'layer_06_position_projection', 'layer_05_position_projection'),
        'layer_07_underlying_action', 'layer_06_underlying_action'),
        'layer_08_option_expression', 'layer_07_option_expression'),
    note = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(note,
        'source_04_event_overlay', 'source_08_event_risk_governor'),
        'feature_04_event_overlay', 'feature_08_event_risk_governor'),
        'feature_08_option_expression', 'feature_07_option_expression'),
        'model_05_alpha_confidence', 'model_04_alpha_confidence'),
        'model_06_position_projection', 'model_05_position_projection'),
        'model_07_underlying_action', 'model_06_underlying_action'),
        'model_08_option_expression', 'model_07_option_expression'),
        'layer_04_event_overlay', 'layer_08_event_risk_governor'),
        'layer_05_alpha_confidence', 'layer_04_alpha_confidence'),
        'layer_06_position_projection', 'layer_05_position_projection'),
        'layer_07_underlying_action', 'layer_06_underlying_action'),
        'layer_08_option_expression', 'layer_07_option_expression'),
    updated_at = NOW()
WHERE key LIKE '%SOURCE_04_EVENT_OVERLAY%'
   OR key LIKE '%FEATURE_04_EVENT_OVERLAY%'
   OR key LIKE '%FEATURE_08_OPTION_EXPRESSION%'
   OR key LIKE '%MODEL_05_ALPHA_CONFIDENCE%'
   OR key LIKE '%MODEL_06_POSITION_PROJECTION%'
   OR key LIKE '%MODEL_07_UNDERLYING_ACTION%'
   OR key LIKE '%MODEL_08_OPTION_EXPRESSION%'
   OR key LIKE '%LAYER_08_OPTION_EXPRESSION%'
   OR payload LIKE '%source_04_event_overlay%'
   OR payload LIKE '%feature_04_event_overlay%'
   OR payload LIKE '%feature_08_option_expression%'
   OR payload LIKE '%model_05_alpha_confidence%'
   OR payload LIKE '%model_06_position_projection%'
   OR payload LIKE '%model_07_underlying_action%'
   OR payload LIKE '%model_08_option_expression%'
   OR payload LIKE '%layer_04_event_overlay%'
   OR payload LIKE '%layer_05_alpha_confidence%'
   OR payload LIKE '%layer_06_position_projection%'
   OR payload LIKE '%layer_07_underlying_action%'
   OR payload LIKE '%layer_08_option_expression%'
   OR payload LIKE '%4_event_%'
   OR payload LIKE '%8_option_%'
   OR path LIKE '%source_04_event_overlay%'
   OR path LIKE '%feature_04_event_overlay%'
   OR path LIKE '%feature_08_option_expression%'
   OR path LIKE '%model_05_alpha_confidence%'
   OR path LIKE '%model_06_position_projection%'
   OR path LIKE '%model_07_underlying_action%'
   OR path LIKE '%model_08_option_expression%'
   OR applies_to LIKE '%source_04_event_overlay%'
   OR applies_to LIKE '%feature_04_event_overlay%'
   OR applies_to LIKE '%feature_08_option_expression%'
   OR applies_to LIKE '%model_05_alpha_confidence%'
   OR applies_to LIKE '%model_06_position_projection%'
   OR applies_to LIKE '%model_07_underlying_action%'
   OR applies_to LIKE '%model_08_option_expression%'
   OR applies_to LIKE '%layer_04_event_overlay%'
   OR applies_to LIKE '%layer_05_alpha_confidence%'
   OR applies_to LIKE '%layer_06_position_projection%'
   OR applies_to LIKE '%layer_07_underlying_action%'
   OR applies_to LIKE '%layer_08_option_expression%'
   OR note LIKE '%source_04_event_overlay%'
   OR note LIKE '%feature_04_event_overlay%'
   OR note LIKE '%feature_08_option_expression%'
   OR note LIKE '%model_05_alpha_confidence%'
   OR note LIKE '%model_06_position_projection%'
   OR note LIKE '%model_07_underlying_action%'
   OR note LIKE '%model_08_option_expression%'
   OR note LIKE '%layer_04_event_overlay%'
   OR note LIKE '%layer_05_alpha_confidence%'
   OR note LIKE '%layer_06_position_projection%'
   OR note LIKE '%layer_07_underlying_action%'
   OR note LIKE '%layer_08_option_expression%';

UPDATE trading_registry
SET payload = replace(replace(replace(replace(replace(replace(replace(payload,
        '5_base_alpha_', '4_base_alpha_'),
        '5_expected_return_', '4_expected_return_'),
        '5_signal_', '4_signal_'),
        '5_path_', '4_path_'),
        '5_reversal_', '4_reversal_'),
        '5_drawdown_', '4_drawdown_'),
        '5_alpha_tradability_', '4_alpha_tradability_'),
    updated_at = NOW()
WHERE payload LIKE '%5_base_alpha_%'
   OR payload LIKE '%5_expected_return_%'
   OR payload LIKE '%5_signal_%'
   OR payload LIKE '%5_path_%'
   OR payload LIKE '%5_reversal_%'
   OR payload LIKE '%5_drawdown_%'
   OR payload LIKE '%5_alpha_tradability_%';

UPDATE trading_registry
SET payload = replace(replace(replace(replace(replace(replace(replace(replace(payload,
        '6_target_', '5_target_'),
        '6_current_', '5_current_'),
        '6_position_', '5_position_'),
        '6_expected_', '5_expected_'),
        '6_cost_', '5_cost_'),
        '6_risk_', '5_risk_'),
        '6_projection_', '5_projection_'),
        '6_resolved_', '5_resolved_'),
    updated_at = NOW()
WHERE payload LIKE '%6_target_%'
   OR payload LIKE '%6_current_%'
   OR payload LIKE '%6_position_%'
   OR payload LIKE '%6_expected_%'
   OR payload LIKE '%6_cost_%'
   OR payload LIKE '%6_risk_%'
   OR payload LIKE '%6_projection_%'
   OR payload LIKE '%6_resolved_%';

UPDATE trading_registry
SET payload = replace(replace(payload,
        '7_underlying_', '6_underlying_'),
        '7_resolved_', '6_resolved_'),
    updated_at = NOW()
WHERE payload LIKE '%7_underlying_%'
   OR payload LIKE '%7_resolved_%';
