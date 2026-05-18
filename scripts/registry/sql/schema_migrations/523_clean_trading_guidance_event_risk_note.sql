-- Clean Layer 8 registry wording so EventRiskGovernor does not appear to depend on Layer 8.

UPDATE trading_registry
SET note = 'Layer 8 model boundary that outputs an optional offline trading-guidance record and optional option-expression context from the Layer 7 direct-underlying thesis. The current V1 option-expression implementation surface is model_08_option_expression; Layer 9 EventRiskGovernor uses Layer 7 underlying_action_plan as the canonical risk target and treats Layer 8 context as optional.',
    updated_at = NOW()
WHERE id = 'trm_TGM001'
  AND key = 'TRADING_GUIDANCE_MODEL';
