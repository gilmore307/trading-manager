-- Clean remaining active registry references after the Layer 8/9 route update.
-- Layer 8 = TradingGuidance / OptionExpression optional expression context.
-- Layer 9 = EventRiskGovernor over the Layer 7 direct-underlying/spot thesis.

UPDATE trading_registry
SET
  id = REPLACE(REPLACE(REPLACE(id,
      'L8EVTCOV', 'L9EVTCOV'),
      'L8ERG', 'L9ERG'),
      'M8ERG', 'M9ERG'),
  key = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(key,
      'LAYER_EIGHT_EVENT', 'LAYER_NINE_EVENT'),
      'MANAGER_LAYER_EIGHT_EVENT', 'MANAGER_LAYER_NINE_EVENT'),
      'MODEL_08_', 'MODEL_09_'),
      'M8ERG', 'M9ERG'),
      'L8ERG', 'L9ERG'),
      'L8EVTCOV', 'L9EVTCOV'),
  payload = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(payload,
      'layer_eight_event_risk_governor', 'layer_nine_event_risk_governor'),
      'manager_layer_eight_event_risk_governor', 'manager_layer_nine_event_risk_governor'),
      'model_08_event_risk_governor', 'model_09_event_risk_governor'),
      'scripts/models/model_08_event_risk_governor', 'scripts/models/model_09_event_risk_governor'),
      'src/models/model_08_event_risk_governor', 'src/models/model_09_event_risk_governor'),
      'MODEL_08_', 'MODEL_09_'),
      '8_event_', '9_event_'),
  path = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(path,
      'layer_eight_event_risk_governor', 'layer_nine_event_risk_governor'),
      'test_layer_eight_event_risk_governor', 'test_layer_nine_event_risk_governor'),
      'model_08_event_risk_governor', 'model_09_event_risk_governor'),
      'scripts/models/model_08_event_risk_governor', 'scripts/models/model_09_event_risk_governor'),
      'src/models/model_08_event_risk_governor', 'src/models/model_09_event_risk_governor'),
      'MODEL_08_', 'MODEL_09_'),
  applies_to = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(applies_to,
      'layer_eight_event_risk_governor', 'layer_nine_event_risk_governor'),
      'manager_layer_eight_event_risk_governor', 'manager_layer_nine_event_risk_governor'),
      'model_08_event_risk_governor', 'model_09_event_risk_governor'),
      '8_event_', '9_event_'),
      'M8ERG', 'M9ERG'),
      'L8ERG', 'L9ERG'),
  note = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(note,
      'Layer 8 event-governor', 'Layer 9 event-governor'),
      'Layer 8 event-source', 'Layer 9 event-source'),
      'Layer 8 event-risk', 'Layer 9 event-risk'),
      'Layer 8 residual event-risk', 'Layer 9 residual event-risk'),
      'layer_eight_event_risk_governor', 'layer_nine_event_risk_governor'),
      'manager_layer_eight_event_risk_governor', 'manager_layer_nine_event_risk_governor'),
      'model_08_event_risk_governor', 'model_09_event_risk_governor'),
      '8_event_', '9_event_'),
  updated_at = NOW()
WHERE id LIKE '%L8EVTCOV%'
   OR id LIKE '%L8ERG%'
   OR id LIKE '%M8ERG%'
   OR key LIKE '%LAYER_EIGHT_EVENT%'
   OR key LIKE '%MODEL_08_%'
   OR key LIKE '%M8ERG%'
   OR key LIKE '%L8ERG%'
   OR key LIKE '%L8EVTCOV%'
   OR payload LIKE '%layer_eight_event_risk_governor%'
   OR payload LIKE '%model_08_event_risk_governor%'
   OR payload LIKE '%8_event_%'
   OR path LIKE '%layer_eight_event_risk_governor%'
   OR path LIKE '%test_layer_eight_event_risk_governor%'
   OR path LIKE '%model_08_event_risk_governor%'
   OR applies_to LIKE '%layer_eight_event_risk_governor%'
   OR applies_to LIKE '%model_08_event_risk_governor%'
   OR applies_to LIKE '%8_event_%'
   OR note LIKE '%Layer 8 event-governor%'
   OR note LIKE '%Layer 8 event-source%'
   OR note LIKE '%Layer 8 event-risk%'
   OR note LIKE '%model_08_event_risk_governor%'
   OR note LIKE '%8_event_%';

UPDATE trading_registry
SET
  key = REPLACE(key, 'LAYER_09_OPTION_EXPRESSION', 'LAYER_08_OPTION_EXPRESSION'),
  payload = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(payload,
      'review_layer_nine_option_expression_gate', 'review_layer_eight_option_expression_gate'),
      'model_09_option_expression', 'model_08_option_expression'),
      'scripts/models/model_09_option_expression', 'scripts/models/model_08_option_expression'),
      'src/models/model_09_option_expression', 'src/models/model_08_option_expression'),
      '9_option_', '8_option_'),
  path = REPLACE(REPLACE(REPLACE(REPLACE(path,
      'review_layer_nine_option_expression_gate', 'review_layer_eight_option_expression_gate'),
      'model_09_option_expression', 'model_08_option_expression'),
      'scripts/models/model_09_option_expression', 'scripts/models/model_08_option_expression'),
      'src/models/model_09_option_expression', 'src/models/model_08_option_expression'),
  applies_to = REPLACE(REPLACE(applies_to,
      'model_09_option_expression', 'model_08_option_expression'),
      '9_option_', '8_option_'),
  note = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(note,
      'Layer 9 trading-guidance', 'Layer 8 trading-guidance'),
      'Layer 9 trading guidance', 'Layer 8 trading guidance'),
      'Layer 9 model boundary', 'Layer 8 model boundary'),
      'Layer 9 scalar/vector output for option-expression', 'Layer 8 scalar/vector output for option-expression'),
      'Accepted current 9_* OptionExpressionModel scalar score-family tokens for Layer 9', 'Accepted current 8_* OptionExpressionModel scalar score-family tokens for Layer 8'),
      'optional Layer 9 trading-guidance/option-expression context', 'optional Layer 8 trading-guidance/option-expression context'),
      'Layer 9 context as downstream', 'Layer 8 context as optional'),
      '9_option_', '8_option_'),
  updated_at = NOW()
WHERE key LIKE '%LAYER_09_OPTION_EXPRESSION%'
   OR payload LIKE '%review_layer_nine_option_expression_gate%'
   OR payload LIKE '%model_09_option_expression%'
   OR payload LIKE '%9_option_%'
   OR path LIKE '%review_layer_nine_option_expression_gate%'
   OR path LIKE '%model_09_option_expression%'
   OR applies_to LIKE '%model_09_option_expression%'
   OR applies_to LIKE '%9_option_%'
   OR note LIKE '%Layer 9 trading-guidance%'
   OR note LIKE '%Layer 9 trading guidance%'
   OR note LIKE '%Layer 9 model boundary%'
   OR note LIKE '%Layer 9 scalar/vector output for option-expression%'
   OR note LIKE '%Accepted current 9_* OptionExpressionModel scalar score-family tokens for Layer 9%'
   OR note LIKE '%optional Layer 9 trading-guidance/option-expression context%'
   OR note LIKE '%Layer 9 context as downstream%'
   OR note LIKE '%9_option_%';

UPDATE trading_registry
SET
  note = 'Layer 9 EventRiskGovernor uses the Layer 7 direct-underlying/spot thesis as the canonical intervention target. Layer 8 trading-guidance and option-expression context are optional; crypto/direct-underlying-only routes must not require option-chain or option-expression evidence.',
  updated_at = NOW()
WHERE id = 'cfg_ERG002';

UPDATE trading_registry
SET
  note = 'Layer 7 boundary policy: UnderlyingActionModel produces an offline direct underlying/spot action thesis for stock, ETF, or crypto-style candidates, with optional Layer 8 trading-guidance handoff. It must not place broker/exchange orders, emit broker order fields, choose option contracts, or mutate broker/account state.',
  updated_at = NOW()
WHERE id = 'cfg_UAPB001';

UPDATE trading_registry
SET
  note = 'Reviewed current 7_* resolved plan/handoff field-family tokens for communicating the Layer 7 direct-underlying action thesis to optional Layer 8 trading guidance and execution-side review. These are not broker order fields.',
  updated_at = NOW()
WHERE id = 'cfg_UAPR001';

UPDATE trading_registry
SET
  note = 'Accepted Layer 9 event-risk governor. It consumes point-in-time residual event evidence with the Layer 7 direct-underlying action thesis as the canonical risk target; optional Layer 8 trading-guidance/option-expression context may be attached when available. It may warn/block/cap/review or emit promotion packets and remains bounded to risk governance unless reviewed evidence moves a family into Layer 4 EventFailureRiskModel.',
  updated_at = NOW()
WHERE id = 'trm_ERG001';

UPDATE trading_registry
SET
  note = 'Layer 8 scalar/vector output for option-expression quality by horizon. It carries eligibility, signed expression direction, contract fit, liquidity fit, IV, Greek fit, reward/risk, theta risk, fill quality, and expression confidence; it is not an order instruction.',
  updated_at = NOW()
WHERE id = 'trm_EXV001';

UPDATE trading_registry
SET
  note = 'Layer 8 model boundary that outputs an optional offline trading-guidance record and optional option-expression context from the Layer 7 direct-underlying thesis. The current V1 option-expression implementation surface is model_08_option_expression; Layer 9 EventRiskGovernor uses Layer 7 underlying_action_plan as the canonical risk target and treats Layer 8 context as optional.',
  updated_at = NOW()
WHERE id = 'trm_TGM001';

UPDATE trading_registry
SET
  note = 'Layer 8 base offline trading-guidance candidate. It can include direct-underlying, option-expression, maintain, or no-trade guidance, but it is not a broker order and does not mutate accounts.',
  updated_at = NOW()
WHERE id = 'trm_TGR001';

UPDATE trading_registry
SET
  note = 'Layer 7 primary offline direct underlying planned action output for stock, ETF, or crypto spot-style candidates. It includes planned action type, effective exposure gap, planned incremental exposure, entry/target/stop/time-stop thesis, risk plan, optional Layer 8 trading-guidance handoff, and reason codes; it is not a broker/exchange order, final order quantity, option contract, or execution instruction.',
  updated_at = NOW()
WHERE id = 'trm_UAP001';
