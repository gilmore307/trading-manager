-- Clean current Layer 8/9 registry wording after option-surface bypass review.

UPDATE trading_registry
SET payload = 'no_option_expression;underlying_only_expression;naive_atm_nearest_expiration_call_put;fixed_delta_fixed_dte_option;layer_9_full_contract_fit_model',
    note = 'Accepted Layer 9 option-expression evaluation baseline ladder. The current physical score/model namespace uses layer_09/model_09. The model must prove value versus no option, underlying-only expression, naive ATM option, fixed delta/DTE option, and full Layer 9 contract-fit model.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_OERB001';

UPDATE trading_registry
SET payload = 'bullish_call_strike_not_above_target_price_high;bearish_put_strike_not_below_target_price_low;apply_only_when_layer_8_target_range_is_directionally_coherent',
    note = 'Accepted Layer 9 V1 moneyness guardrail. Layer 9 uses Layer 8 target range to prevent lottery-like call strikes above coherent bullish target highs and put strikes below coherent bearish target lows. This is still offline model evidence and not broker routing.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_OEMG001';

UPDATE trading_registry
SET note = 'Layer 8 SQL-backed generator reads completed Layer 7 position-projection rows and matching Layer 5 alpha-confidence rows, then persists trading_model.model_08_underlying_action using local point-in-time default quote/liquidity/risk context; it remains offline planning only and performs no provider calls, model activation, broker execution, or storage lifecycle mutation.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'scr_L7DB001';

UPDATE trading_registry
SET note = 'Current 9_* score-family token for Layer 9 option-expression: selected contract fit to the Layer 8 path thesis and option-expression constraints by horizon.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'fld_OEV1003';
