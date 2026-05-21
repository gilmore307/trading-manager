-- Clean the remaining active layer-number notes after the 10-layer manager review.

UPDATE trading_registry
SET note = 'Accepted conservative Layer 9 V1 delta policy for single-leg long call/put expression. Future learned fit models may adjust by path quality, expected move, IV, liquidity, and theta pressure.',
    updated_at = NOW()
WHERE id = 'cfg_OEDLT001';

UPDATE trading_registry
SET note = 'Accepted Layer 9 V1 option-expression type vocabulary. Current physical model_09/9_* names are active. V1 supports single-leg long call, single-leg long put, underlying-only expression fallback, and no-option-expression outcomes.',
    updated_at = NOW()
WHERE id = 'cfg_OEPT001';

UPDATE trading_registry
SET note = 'Layer 5 AlphaConfidence using current 5_* field tokens final adjusted alpha-level suitability score for Layer 6 dynamic-risk policy, Layer 7 position projection, and Layer 8 underlying-action planning by horizon; this is not target exposure, planned quantity, an order instruction, option expression, or final approval.',
    updated_at = NOW()
WHERE id = 'fld_ACMV1009';

UPDATE trading_registry
SET note = 'Accepted Layer 9 option-expression model id. OptionExpressionModel consumes Layer 8 underlying path assumptions plus point-in-time option-chain context and emits offline option_expression_plan / expression_vector rows; current physical surface is model_09_option_expression.',
    updated_at = NOW()
WHERE id = 'trm_OEM001';
