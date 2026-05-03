UPDATE trading_registry
SET path = CASE path
  WHEN 'trading-model/docs/07_system_model_architecture_rfc.md' THEN 'trading-model/docs/90_system_model_architecture_rfc.md'
  WHEN 'trading-model/docs/91_layer_01_market_regime.md' THEN 'trading-model/docs/02_layer_01_market_regime.md'
  WHEN 'trading-model/docs/92_layer_02_sector_context.md' THEN 'trading-model/docs/03_layer_02_sector_context.md'
  WHEN 'trading-model/docs/05_decision.md' THEN 'trading-model/docs/81_decision.md'
  WHEN 'trading-data/docs/11_model_inputs.md' THEN 'trading-data/docs/94_model_inputs.md'
  WHEN 'trading-manager/docs/08_registry.md' THEN 'trading-manager/docs/91_registry.md'
  WHEN 'trading-manager/docs/07_helpers.md' THEN 'trading-manager/docs/90_helpers.md'
  WHEN 'trading-manager/docs/09_templates.md' THEN 'trading-manager/docs/92_templates.md'
  ELSE path
END,
updated_at = NOW()
WHERE path IN (
  'trading-model/docs/07_system_model_architecture_rfc.md',
  'trading-model/docs/91_layer_01_market_regime.md',
  'trading-model/docs/92_layer_02_sector_context.md',
  'trading-model/docs/05_decision.md',
  'trading-data/docs/11_model_inputs.md',
  'trading-manager/docs/08_registry.md',
  'trading-manager/docs/07_helpers.md',
  'trading-manager/docs/09_templates.md'
);
