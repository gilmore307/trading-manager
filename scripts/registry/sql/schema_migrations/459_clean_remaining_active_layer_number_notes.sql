-- Clean active registry notes whose prose still described pre-renumbering conceptual layers.
-- Historical migration files and audit/decision history intentionally remain unchanged.

UPDATE trading_registry
SET note = 'Reviewed Layer 4 base/unadjusted Layer 1/2/3 alpha diagnostic score-family tokens. These are research/audit/event-attribution diagnostics, not default Layer 5-facing state_vector_value rows.',
    updated_at = NOW()
WHERE id = 'cfg_ACVBD001';

UPDATE trading_registry
SET note = 'Reviewed Layer 4 baseline-adjustment diagnostic score-family tokens for separating target-specific alpha from market/sector beta. These are research/audit diagnostics, not default Layer 5-facing state_vector_value rows.',
    updated_at = NOW()
WHERE id = 'cfg_ACVBA001';

UPDATE trading_registry
SET note = 'Reviewed Layer 4 event-attribution diagnostic field-family tokens for attributing how EventRiskGovernor context changed base alpha. These are research/audit diagnostics and reason-code fields, not default Layer 5-facing state_vector_value rows.',
    updated_at = NOW()
WHERE id = 'cfg_ACVEA001';

UPDATE trading_registry
SET payload = replace(payload, 'layer_8_full_contract_fit_model', 'layer_7_full_contract_fit_model'),
    note = 'Accepted Layer 7 option-expression evaluation baseline ladder. Layer 7 must prove value versus no option, underlying-only expression, naive ATM option, fixed delta/DTE option, and full contract-fit model.',
    updated_at = NOW()
WHERE id = 'cfg_OERB001';

UPDATE trading_registry
SET note = 'Reviewed Layer 5 diagnostic field-family tokens for raw alpha-to-position priors, effective exposure calculations, and risk/cost reason-code attribution. Diagnostics are not default Layer 6-facing state_vector_value rows.',
    updated_at = NOW()
WHERE id = 'cfg_PPVD001';

UPDATE trading_registry
SET note = 'Layer 4 SQL-backed generator reads completed Layer 3/upstream state rows and persists trading_model.model_04_alpha_confidence without provider calls, model activation, broker execution, or storage lifecycle mutation.',
    updated_at = NOW()
WHERE id = 'scr_L5DB001';

UPDATE trading_registry
SET note = 'Layer 5 SQL-backed generator reads completed Layer 4 alpha-confidence rows and persists trading_model.model_05_position_projection using flat/no-pending position context defaults; it performs no provider calls, model activation, broker execution, or storage lifecycle mutation.',
    updated_at = NOW()
WHERE id = 'scr_L6DB001';

UPDATE trading_registry
SET note = 'Layer 6 SQL-backed generator reads completed Layer 4/5 rows and persists trading_model.model_06_underlying_action using local point-in-time default quote/liquidity/risk context; it remains offline planning only and performs no provider calls, model activation, broker execution, or storage lifecycle mutation.',
    updated_at = NOW()
WHERE id = 'scr_L7DB001';

UPDATE trading_registry
SET note = 'Layer 5 high-is-bad score family for relative cost pressure required to close the position gap by horizon. It is not a no-trade action.',
    updated_at = NOW()
WHERE id = 'fld_PPV1007';

UPDATE trading_registry
SET note = 'Layer 5 signed score family for expected risk-adjusted net utility of the projected target holding state after position-level friction and risk penalties.',
    updated_at = NOW()
WHERE id = 'fld_PPV1006';

UPDATE trading_registry
SET note = 'Layer 5 signed score family for target exposure minus effective current exposure by horizon. This is a state gap, not an execution instruction.',
    updated_at = NOW()
WHERE id = 'fld_PPV1004';

UPDATE trading_registry
SET note = 'Layer 5 model-local exposure construct: current_position_exposure plus pending_exposure_size times pending_order_fill_probability_estimate. Used to compute position gap; not an execution instruction.',
    updated_at = NOW()
WHERE id = 'trm_ECE001';

UPDATE trading_registry
SET note = 'Layer 6 model-local exposure construct: current direct-underlying exposure plus pending underlying exposure times pending fill probability estimate. Used to compute underlying exposure gap and avoid duplicate plans; not an execution instruction.',
    updated_at = NOW()
WHERE id = 'trm_ECUE01';
