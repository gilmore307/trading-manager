-- Refresh remaining option-expression registry notes after conceptual layer reorder.
-- Names with layer_08 / 8_* remain legacy physical tokens until a dedicated rename migration.

UPDATE trading_registry
SET note = 'Manager-owned legacy layer_08_option_expression feature-stage adapter for conceptual Layer 7 option-expression. It writes a first-class no-provider/no-feature skip receipt when the reviewed gate has zero active target chains, or delegates to trading-data feature_08 option-expression generation after approved active-path acquisition.',
    updated_at = NOW()
WHERE id = 'scr_L8FEAT001';

UPDATE trading_registry
SET note = 'Manager-owned review for legacy layer_08_option_expression acquisition at the conceptual Layer 7 option-expression boundary. Active target chains are prepared for autonomous option-snapshot acquisition; no manual provider gate is required.',
    updated_at = NOW()
WHERE id IN ('scr_L8GATE001', 'term_L8GATE001');

UPDATE trading_registry
SET note = 'Legacy 8_* score-family token for conceptual Layer 7 option-expression: selected contract fit to the Layer 6 path thesis and option-expression constraints by horizon.',
    updated_at = NOW()
WHERE id = 'fld_OEV1003';

UPDATE trading_registry
SET note = 'Legacy 8_* score-family token for conceptual Layer 7 option-expression: calibrated confidence in the complete offline option-expression plan by horizon. This is not final approval or execution authorization.',
    updated_at = NOW()
WHERE id = 'fld_OEV1010';

UPDATE trading_registry
SET note = 'Legacy 8_* signed score-family token for conceptual Layer 7 option-expression direction by horizon. Positive is call-side/bullish expression, negative is put-side/bearish expression, near zero is no-option expression; this is not order routing.',
    updated_at = NOW()
WHERE id = 'fld_OEV1002';

UPDATE trading_registry
SET note = 'Legacy 8_* high-is-good score-family token for conceptual Layer 7 option-expression admissibility after Layer 6 thesis, policy, option-chain, liquidity, IV, and risk constraints by horizon. This is not final approval.',
    updated_at = NOW()
WHERE id = 'fld_OEV1001';
