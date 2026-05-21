-- Align the remaining option-expression layer-policy registry row to the current Layer 9 surface.

UPDATE trading_registry
SET payload = replace(replace(payload,
        'layer_08_after_underlying_action', 'layer_09_after_underlying_action'),
        'model_08_physical_surface', 'model_09_physical_surface'),
    note = 'Layer policy for OptionExpressionModel: option expression is Layer 9 optional expression context, consumes Layer 8 underlying path assumptions plus option-chain context when available, and remains offline without broker mutation. Current physical names use model_09/9_*.',
    updated_at = NOW()
WHERE key = 'OPTION_EXPRESSION_MODEL_LAYER_POLICY';

