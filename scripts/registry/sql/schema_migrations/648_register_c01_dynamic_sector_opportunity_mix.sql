-- Register dynamic C01 sector opportunity mix semantics.

UPDATE trading_registry
SET note = 'C01 Intake field listing sufficiently strong sectors/themes with target, current, and remaining opportunity weights derived from M02 relative strength and current sleeve holdings. C01 subtracts already-filled sector mix so C02 receives the remaining opportunity map, not a final position weight, order quantity, or risk allocation instruction.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'fld_EXECRTC011';

UPDATE trading_registry
SET note = 'Execution runtime contract emitted by C01 Intake for account balance state, current holdings, watch targets, dynamic remaining sector opportunity mix, and account-sleeve candidate filtering. It does not allocate risk budget, size positions, decide entries, manage exits, construct orders, or mutate broker/account state.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'art_EXECRTC003';

UPDATE trading_registry
SET note = 'Policy stating live trading and Replay use the same execution component graph and decision contracts, with only adapter profiles swapped. C01 Intake reads account state, current holdings, watch targets, and dynamic remaining sector opportunity mix only; it does not allocate risk budget or manage positions. trading-evaluation owns orchestration and judgment, not duplicated trading decisions. Runtime decisions must keep crypto and equity/options in independent account sleeves without cross-account collateral, buying-power, position, or risk-budget netting.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_EXECRTC001';
