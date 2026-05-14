-- Correct the reviewed initial Layer 3+ target to a single stock.
-- SPY remains valid market-state/panel evidence by default and should only be
-- used as a downstream target when explicitly reviewed as such.

UPDATE trading_registry
SET payload = 'AAPL',
    note = 'Reviewed initial single-stock target symbol for the first Layer 3+ six-month dataset unit in the service template. SPY remains market-state/panel evidence by default; operators may explicitly override the target for later reviewed target expansion.',
    updated_at = NOW()
WHERE id = 'cfg_DU002';

UPDATE trading_registry
SET note = 'Formal workflow progression is segmented by dataset unit: Layers 1-2 are finite six-month panel flows with no single target symbol; Layers 3-7 run target-major one selected single-stock target symbol over one six-month unit before the next target by default; Layer 8 option-expression expansion waits for the completed upstream target chain. Layer 3+ task plans must expose selected_target_symbol and block with selected_target_symbol_required when omitted.',
    updated_at = NOW()
WHERE id = 'cfg_MWFP002';
