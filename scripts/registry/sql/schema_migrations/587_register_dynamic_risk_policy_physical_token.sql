-- Register the DynamicRiskPolicyModel physical token expected by layer-token governance.

UPDATE trading_registry
SET applies_to = 'layer_06_dynamic_risk_policy;model_06_dynamic_risk_policy;position_projection;option_expression;event_risk_governor;portfolio_context_state',
    note = 'DynamicRiskPolicyModel is inserted as conceptual Layer 6 with physical token model_06_dynamic_risk_policy. It learns dynamic premium/risk-budget policy mainly from Layer 1 global market regime plus systemic/broad event risk and portfolio context. Target-specific evidence can cap the current target but must not distort global risk budget. Execution hard order gates remain outside the model stack.',
    updated_at = NOW()
WHERE key = 'DYNAMIC_RISK_POLICY_MODEL_LAYER';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'layer_06_dynamic_risk_policy;model_06_position_projection', 'layer_06_dynamic_risk_policy;model_06_dynamic_risk_policy;model_06_position_projection'),
    updated_at = NOW()
WHERE key = 'MANAGER_MODEL_TRAINING_WORKFLOW_PLAN_ARTIFACT';
