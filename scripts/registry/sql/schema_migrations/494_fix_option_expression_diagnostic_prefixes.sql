-- Correct active OptionExpressionModel diagnostic field-family prefixes after the nine-layer physical alignment.
-- Layer 8 option-expression/trading-guidance diagnostics use 8_* prefixes.

UPDATE trading_registry
SET payload = '8_candidate_count;8_eligible_candidate_count;8_candidate_hard_filter_fail_reason_codes;8_contract_dte_fit_score;8_contract_spread_pct;8_contract_iv_rank;8_premium_risk_reason_codes;8_option_expression_reason_codes',
    note = 'Reviewed Layer 8 diagnostic field-family tokens for candidate counts, per-candidate hard-filter reason codes, contract fit attribution, premium-risk attribution, and expression reason codes. Diagnostics are not default scalar score-family rows.',
    updated_at = NOW()
WHERE id = 'cfg_OEPD001';
