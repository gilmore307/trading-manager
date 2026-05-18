-- Fix active registry notes after the Layer 8/9 active surface alignment.
-- Migration 524 was already applied locally, so these note-only corrections live here.

UPDATE trading_registry
SET note = 'Reviewed current 7_* resolved plan/handoff field-family tokens for communicating the Layer 7 direct-underlying action thesis to Layer 9 trading guidance and execution-side review. These are not broker order fields.',
    updated_at = NOW()
WHERE id = 'cfg_UAPR001';

UPDATE trading_registry
SET note = 'Layer 9 scalar/vector output for option-expression quality by horizon. It carries eligibility, signed expression direction, contract fit, liquidity fit, IV, Greek fit, reward/risk, theta risk, fill quality, and expression confidence; it is not an order instruction.',
    updated_at = NOW()
WHERE id = 'trm_EXV001';
