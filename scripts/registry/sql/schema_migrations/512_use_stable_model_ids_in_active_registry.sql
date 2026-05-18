-- Use stable semantic model ids in active model-promotion registry payloads.
-- Physical model_NN names remain valid for script paths, SQL table/surface terms,
-- and historical migration audit records; active promotion-control-plane ids use
-- stable ids only.

UPDATE trading_registry
SET payload = 'market_regime_model;sector_context_model;target_state_vector_model;event_failure_risk_model;alpha_confidence_model;position_projection_model;underlying_action_model;option_expression_model;event_risk_governor',
    note = 'Canonical stable model ids accepted by the unified manager-side promotion review request planner, ordered by current conceptual layer order. Physical model_NN names are implementation paths or SQL surfaces, not promotion-control-plane ids.',
    updated_at = NOW()
WHERE key = 'MODEL_PROMOTION_UNIFIED_TARGETS';

UPDATE trading_registry
SET payload = replace(payload, 'layer_3:model_03_target_state_vector:', 'layer_3:target_state_vector_model:'),
    updated_at = NOW()
WHERE key = 'MODEL_LAYER_03_PRODUCTION_EVAL_SUBSTRATE_RECEIPT';

UPDATE trading_registry
SET payload = replace(replace(replace(replace(replace(replace(replace(replace(payload,
      'layer_1:model_01_market_regime:', 'layer_1:market_regime_model:'),
      'layer_2:model_02_sector_context:', 'layer_2:sector_context_model:'),
      'layer_3:model_03_target_state_vector:', 'layer_3:target_state_vector_model:'),
      'layer_4:model_05_alpha_confidence:', 'layer_4:alpha_confidence_model:'),
      'layer_5:model_06_position_projection:', 'layer_5:position_projection_model:'),
      'layer_6:model_07_underlying_action:', 'layer_6:underlying_action_model:'),
      'layer_7:model_08_option_expression:', 'layer_7:option_expression_model:'),
      'layer_8:model_09_event_risk_governor:', 'layer_8:event_risk_governor:'),
    updated_at = NOW()
WHERE key = 'MODEL_PROMOTION_ACCEPTANCE_DECISION_RECEIPTS';
