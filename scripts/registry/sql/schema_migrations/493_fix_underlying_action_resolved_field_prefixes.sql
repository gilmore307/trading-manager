-- Correct the active UnderlyingActionModel resolved-field payload after bulk physical renumbering.
-- Layer 7 underlying-action handoff fields use 7_* prefixes; Layer 8 is the downstream option-expression/trading-guidance boundary.

UPDATE trading_registry
SET payload = '7_resolved_underlying_action_type;7_resolved_action_side;7_resolved_dominant_horizon;7_resolved_trade_eligibility_score;7_resolved_trade_intensity_score;7_resolved_entry_quality_score;7_resolved_action_confidence_score;7_resolved_reason_codes',
    note = 'Reviewed current 7_* resolved plan/handoff field-family tokens for communicating the Layer 7 direct-underlying action thesis to Layer 8 trading guidance and execution-side review. These are not broker order fields.',
    updated_at = NOW()
WHERE id = 'cfg_UAPR001';
