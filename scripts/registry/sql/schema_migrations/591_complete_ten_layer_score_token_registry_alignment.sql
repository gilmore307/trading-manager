-- Complete score-token registry alignment after the active 10-layer physical cutover.

UPDATE trading_registry
SET payload = replace(payload, 'layer_09_event_risk_governor_event_not_new_model_layer', 'layer_10_event_risk_governor_event_not_new_model_layer'),
    note = replace(note, 'Layer 9 event', 'Layer 10 event'),
    updated_at = NOW()
WHERE key = 'PRICE_ACTION_EVENT_LAYER_POLICY';

UPDATE trading_registry
SET payload = replace(payload, '6_', '7_'),
    note = replace(replace(note, 'Layer 6 PositionProjectionModel', 'Layer 7 PositionProjectionModel'), 'Layer 6 target holding-state projection', 'Layer 7 target holding-state projection'),
    updated_at = NOW()
WHERE kind = 'state_vector_value'
  AND (
    payload LIKE '6_target_%'
    OR payload LIKE '6_current_position_%'
    OR payload LIKE '6_position_%'
    OR payload LIKE '6_expected_position_%'
    OR payload LIKE '6_cost_%'
    OR payload LIKE '6_risk_budget_%'
    OR payload LIKE '6_projection_%'
  );

UPDATE trading_registry
SET payload = replace(payload, '7_underlying_', '8_underlying_'),
    note = replace(note, 'Layer 7 UnderlyingActionModel', 'Layer 8 UnderlyingActionModel'),
    updated_at = NOW()
WHERE kind = 'state_vector_value'
  AND payload LIKE '7_underlying_%';

UPDATE trading_registry
SET payload = replace(payload, '8_option_', '9_option_'),
    note = replace(note, 'Layer 8 OptionExpressionModel', 'Layer 9 OptionExpressionModel'),
    updated_at = NOW()
WHERE kind = 'state_vector_value'
  AND payload LIKE '8_option_%';

