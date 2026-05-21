-- Finish active registry cleanup found by the Codex 5.5 manager re-review.

UPDATE trading_registry
SET note = '10 control-plane-facing EventRiskGovernor data source; prepares one SQL event overview row per required event with details behind references.',
    updated_at = NOW()
WHERE id = 'dbu_PRKINPUT';

UPDATE trading_registry
SET payload = 'trading-data-feature-09-option-expression',
    updated_at = NOW()
WHERE id = 'scr_F8OEGEN';

UPDATE trading_registry
SET payload = 'trading-data-feature-10-event-risk-governor',
    updated_at = NOW()
WHERE id = 'scr_F4EOGEN';

UPDATE trading_registry
SET note = 'Refreshes the durable base Layer 1-10 workflow checkpoint, ingests component receipts, records review refs, and selects the next safe or guarded stage without provider calls, model activation, broker execution, or event-risk gating.',
    updated_at = NOW()
WHERE id = 'scr_MMTW002';

UPDATE trading_registry
SET note = 'Prints the current base Layer 1-10 manager historical-training workflow graph and next gated stage without provider calls, model activation, broker execution, or event-risk gating.',
    updated_at = NOW()
WHERE id = 'scr_MMTW001';

UPDATE trading_registry
SET note = replace(note, 'Layer 8 high-is-good score family', 'Layer 9 high-is-good score family'),
    updated_at = NOW()
WHERE id IN ('fld_OEV1004', 'fld_OEV1005', 'fld_OEV1006', 'fld_OEV1007', 'fld_OEV1009');

UPDATE trading_registry
SET note = replace(note, 'Layer 8 high-is-bad score family', 'Layer 9 high-is-bad score family'),
    updated_at = NOW()
WHERE id = 'fld_OEV1008';

UPDATE trading_registry
SET note = 'Layer 9 scalar/vector output for option-expression quality by horizon. It carries eligibility, signed expression direction, contract fit, liquidity fit, IV, Greek fit, reward/risk, theta risk, fill quality, and expression confidence; it is not an order instruction.',
    updated_at = NOW()
WHERE id = 'trm_EXV001';

UPDATE trading_registry
SET note = 'Layer 9 point-in-time option-chain snapshot reference used to replay why a selected contract was chosen. This is not a broker order id.',
    updated_at = NOW()
WHERE id = 'trm_OQSR001';

UPDATE trading_registry
SET note = 'Layer 9 primary offline option-expression output. It includes selected expression type, selected option right, point-in-time selected contract reference, contract constraints, premium-risk plan, underlying thesis reference, reason codes, and diagnostics; it is not a broker order or account mutation.',
    updated_at = NOW()
WHERE id = 'trm_OEP001';

UPDATE trading_registry
SET note = 'Layer 9 point-in-time pending option exposure context used to avoid duplicate option-expression plans. It is not a new order instruction.',
    updated_at = NOW()
WHERE id = 'trm_POEC001';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'layer_08_trading_guidance', 'layer_09_trading_guidance'),
    updated_at = NOW()
WHERE id IN ('trm_TGM001', 'trm_TGR001');

UPDATE trading_registry
SET note = 'Layer 9 base offline trading-guidance candidate. It can include direct-underlying, option-expression, maintain, or no-trade guidance, but it is not a broker order and does not mutate accounts.',
    updated_at = NOW()
WHERE id = 'trm_TGR001';

UPDATE trading_registry
SET note = replace(note, 'Layer 1-8', 'Layer 1-10'),
    updated_at = NOW()
WHERE id IN (
  'trm_EXEC_RT006',
  'trm_EXEC_RT007',
  'trm_EXEC_RT008',
  'trm_EXEC_RT009',
  'trm_MODEL_RTD001',
  'trm_MODEL_RTD002',
  'trm_MODEL_RTD003',
  'trm_MRTD001'
)
  AND note LIKE '%Layer 1-8%';
