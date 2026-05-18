-- Align active registry rows with the accepted current route.
-- Layer 8 is TradingGuidance / OptionExpression optional expression context.
-- Layer 9 is EventRiskGovernor over the Layer 7 direct-underlying/spot thesis.
-- Historical migrations remain unchanged for auditability.

UPDATE trading_registry
SET
  key = REPLACE(key, 'MODEL_08_EVENT', 'MODEL_09_EVENT'),
  payload = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(payload,
      'model_08_event_risk_governor', 'model_09_event_risk_governor'),
      'layer_08_event_risk_governor', 'layer_09_event_risk_governor'),
      '8_event_', '9_event_'),
      'model_09_physical_surface', 'model_08_physical_surface'),
      'layer_09_trading_guidance', 'layer_08_trading_guidance'),
  path = REPLACE(REPLACE(REPLACE(path,
      'trading-model/docs/17_layer_08_event_risk_governor.md', 'trading-model/docs/18_layer_09_event_risk_governor.md'),
      'trading-model/docs/18_layer_09_trading_guidance.md', 'trading-model/docs/17_layer_08_trading_guidance.md'),
      'trading-model/docs/18_layer_08_trading_guidance.md', 'trading-model/docs/17_layer_08_trading_guidance.md'),
  applies_to = REPLACE(REPLACE(REPLACE(REPLACE(applies_to,
      'model_08_event_risk_governor', 'model_09_event_risk_governor'),
      'layer_08_event_risk_governor', 'layer_09_event_risk_governor'),
      '8_event_', '9_event_'),
      'layer_09_trading_guidance', 'layer_08_trading_guidance'),
  note = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(note,
      'Layer 8 EventRiskGovernor', 'Layer 9 EventRiskGovernor'),
      'Layer 8 event-risk-governor', 'Layer 9 event-risk-governor'),
      'Layer 8 event-risk governor', 'Layer 9 event-risk governor'),
      'Layer 8 event-risk', 'Layer 9 event-risk'),
      'Layer 8 residual event-risk', 'Layer 9 residual event-risk'),
      'Layer 8 point-in-time event-context', 'Layer 9 point-in-time event-context'),
      'model_08_event_risk_governor', 'model_09_event_risk_governor'),
      'layer_08_event_risk_governor', 'layer_09_event_risk_governor'),
      '8_event_', '9_event_'),
      'Layer 9 TradingGuidance', 'Layer 8 TradingGuidance'),
      'Layer 9 OptionExpressionModel', 'Layer 8 OptionExpressionModel'),
      'Layer 9 option-expression', 'Layer 8 option-expression'),
  updated_at = NOW()
WHERE key LIKE '%MODEL_08_EVENT%'
   OR payload LIKE '%model_08_event_risk_governor%'
   OR payload LIKE '%layer_08_event_risk_governor%'
   OR payload LIKE '%8_event_%'
   OR payload LIKE '%model_09_physical_surface%'
   OR payload LIKE '%layer_09_trading_guidance%'
   OR path LIKE '%17_layer_08_event_risk_governor%'
   OR path LIKE '%18_layer_09_trading_guidance%'
   OR path LIKE '%18_layer_08_trading_guidance%'
   OR applies_to LIKE '%model_08_event_risk_governor%'
   OR applies_to LIKE '%layer_08_event_risk_governor%'
   OR applies_to LIKE '%8_event_%'
   OR applies_to LIKE '%layer_09_trading_guidance%'
   OR note LIKE '%Layer 8 EventRiskGovernor%'
   OR note LIKE '%Layer 8 event-risk%'
   OR note LIKE '%Layer 8 residual event-risk%'
   OR note LIKE '%Layer 8 point-in-time event-context%'
   OR note LIKE '%model_08_event_risk_governor%'
   OR note LIKE '%layer_08_event_risk_governor%'
   OR note LIKE '%8_event_%'
   OR note LIKE '%Layer 9 TradingGuidance%'
   OR note LIKE '%Layer 9 OptionExpressionModel%'
   OR note LIKE '%Layer 9 option-expression%';

UPDATE trading_registry
SET
  key = REPLACE(key, 'MODEL_09_OPTION', 'MODEL_08_OPTION'),
  payload = REPLACE(REPLACE(REPLACE(REPLACE(payload,
      'model_09_option_expression', 'model_08_option_expression'),
      'layer_09_option_expression', 'layer_08_option_expression'),
      '9_option_', '8_option_'),
      'model_09/9_*', 'model_08/8_*'),
  applies_to = REPLACE(REPLACE(REPLACE(applies_to,
      'model_09_option_expression', 'model_08_option_expression'),
      'layer_09_option_expression', 'layer_08_option_expression'),
      '9_option_', '8_option_'),
  note = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(note,
      'Layer 9 V1 option-expression', 'Layer 8 V1 option-expression'),
      'Layer 9 V1 delta', 'Layer 8 V1 delta'),
      'Layer 9 V1 DTE', 'Layer 8 V1 DTE'),
      'Layer 9 V1 moneyness', 'Layer 8 V1 moneyness'),
      'Layer 9 primary offline option-expression', 'Layer 8 primary offline option-expression'),
      'Layer 9 point-in-time option-chain', 'Layer 8 point-in-time option-chain'),
      'Layer 9 point-in-time pending option exposure', 'Layer 8 point-in-time pending option exposure'),
      'Layer 9 owns option expression', 'Layer 8 owns option expression'),
      'Layer 9 owns trading guidance / option expression', 'Layer 8 owns trading guidance / option expression'),
      'model_09/9_*', 'model_08/8_*'),
      '9_option_', '8_option_'),
  updated_at = NOW()
WHERE key LIKE '%MODEL_09_OPTION%'
   OR payload LIKE '%model_09_option_expression%'
   OR payload LIKE '%layer_09_option_expression%'
   OR payload LIKE '%9_option_%'
   OR payload LIKE '%model_09/9_*%'
   OR applies_to LIKE '%model_09_option_expression%'
   OR applies_to LIKE '%layer_09_option_expression%'
   OR applies_to LIKE '%9_option_%'
   OR note LIKE '%Layer 9 V1 option-expression%'
   OR note LIKE '%Layer 9 V1 delta%'
   OR note LIKE '%Layer 9 V1 DTE%'
   OR note LIKE '%Layer 9 V1 moneyness%'
   OR note LIKE '%Layer 9 primary offline option-expression%'
   OR note LIKE '%Layer 9 point-in-time option-chain%'
   OR note LIKE '%Layer 9 point-in-time pending option exposure%'
   OR note LIKE '%Layer 9 owns option expression%'
   OR note LIKE '%Layer 9 owns trading guidance / option expression%'
   OR note LIKE '%model_09/9_*%'
   OR note LIKE '%9_option_%';

UPDATE trading_registry
SET
  payload = 'layer_01_market_regime;layer_02_sector_context;layer_03_target_state_vector;layer_04_event_failure_risk;layer_05_alpha_confidence;layer_06_position_projection;layer_07_underlying_action;layer_08_trading_guidance;layer_09_event_risk_governor',
  note = 'Active layer order after the accepted route update: Layer 8 is TradingGuidance / OptionExpression optional expression context; Layer 9 is EventRiskGovernor / EventIntelligenceOverlay for event-risk governance of the Layer 7 direct-underlying thesis. Active script/package/table names use the current nine-layer numbering; historical/applied migration records may retain prior names.',
  updated_at = NOW()
WHERE id = 'cfg_MLRP003';

UPDATE trading_registry
SET
  note = 'Manager-owned base Layer 1-9 workflow plan within the resident Layer 1-9 historical-modeling system service. During foundation catch-up, month-scoped workflow states expose only reusable substrate data_acquisition and feature_generation for Layers 1-2 before target-specific work; base model generation/evaluation/Promotion Review belong to fold-scoped model/promotion work after frozen 4+1+1 manifests exist. Current source_09_event_risk_governor / Layer 9 EventRiskGovernor governs the Layer 7 direct-underlying thesis; Layer 8 trading-guidance/option-expression context is optional.',
  updated_at = NOW()
WHERE id = 'art_MMTW001';

UPDATE trading_registry
SET
  payload = 'layer_08_after_underlying_action;uses_underlying_action_plan;uses_option_chain_context;no_broker_mutation;model_08_physical_surface',
  note = 'Layer policy for OptionExpressionModel: option expression is Layer 8 optional expression context, consumes Layer 7 underlying path assumptions plus option-chain context when available, and remains offline without broker mutation. Current physical names use model_08/8_*.',
  updated_at = NOW()
WHERE id = 'cfg_OEML001';

UPDATE trading_registry
SET
  note = 'Layer 9 point-in-time event-context / event-risk-governor evidence output. It contains event timing, scope, type, intensity, directional context, risk context, and quality context without action or execution instructions; it is not a hard upstream alpha prerequisite.',
  updated_at = NOW()
WHERE id = 'trm_ECV001';

UPDATE trading_registry
SET
  note = 'Layer 8 point-in-time option-chain snapshot reference used to replay why a selected contract was chosen. This is not a broker order id.',
  updated_at = NOW()
WHERE id = 'trm_OQSR001';
