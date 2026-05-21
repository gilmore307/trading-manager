-- Align the active option-expression boundary note with the current Layer 9 physical surface.

UPDATE trading_registry
SET note = 'Layer 9 option-expression boundary policy: OptionExpressionModel produces an offline option-expression plan and expression vector. Current physical model_09/9_* names are active. It may resolve to underlying-only expression when the Layer 8 thesis remains usable without an option contract. It must not place orders, emit broker order fields, choose route/time-in-force, emit final order quantity, or mutate broker/account state.',
    updated_at = NOW()
WHERE id = 'cfg_OEPB001';
