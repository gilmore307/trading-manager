-- Align conceptual Layer 9 token with the stable option-expression promotion layer.

UPDATE trading_registry
SET payload = 'layer_01_market_regime;layer_02_sector_context;layer_03_target_state_vector;layer_04_event_failure_risk;layer_05_alpha_confidence;layer_06_dynamic_risk_policy;layer_07_position_projection;layer_08_underlying_action;layer_09_option_expression;layer_10_event_risk_governor',
    note = 'Active layer order after the accepted route update: Layer 6 is DynamicRiskPolicyModel; Layer 9 is TradingGuidance / OptionExpression optional expression context and uses stable layer token layer_09_option_expression; Layer 10 is EventRiskGovernor / EventIntelligenceOverlay for event-risk governance of the Layer 8 direct-underlying thesis. Downstream physical script/package/table names may retain older Layer 6-9 numbering until dedicated renumbering; historical/applied migration records may retain prior names.',
    updated_at = NOW()
WHERE key = 'MODEL_LAYER_CONCEPTUAL_REORDER_POLICY';
