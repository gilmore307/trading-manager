-- Fix active registry rows found during the Codex 5.5 manager review.

UPDATE trading_registry
SET note = 'Manager-owned base Layer 1-10 workflow plan within the resident historical-modeling system service. Active workflow commands route directly to the current 10-layer model packages. During foundation catch-up, month-scoped workflow states expose only reusable substrate data_acquisition and feature_generation for Layers 1-2 before target-specific work; base model generation/evaluation/promotion review belong to fold-scoped model/promotion work after frozen 4+1+1 manifests exist.',
    updated_at = NOW()
WHERE id = 'art_MMTW001';

UPDATE trading_registry
SET note = 'Manager-owned durable base Layer 1-10 workflow state within the resident historical-modeling system service. Month-scoped checkpoints count foundation catch-up progress from reusable Layer 1/2 data acquisition and feature generation substrate, allowing chronological advancement before target-specific Layers 3-10 scheduling.',
    updated_at = NOW()
WHERE id = 'art_MMTW002';

UPDATE trading_registry
SET payload = 'current_physical_surfaces_aligned_with_ten_layer_order;historical_migrations_and_artifacts_unchanged',
    note = 'Active script/table/package/stage names use model_08_underlying_action for UnderlyingActionModel, model_09_option_expression for TradingGuidance/OptionExpression, and model_10_event_risk_governor for EventRiskGovernor. Historical/applied migrations and old artifacts remain unchanged for auditability.',
    updated_at = NOW()
WHERE id = 'cfg_LPNM001';

UPDATE trading_registry
SET note = 'Narrow startup abnormality scope for Layer 10 event-activity bridge evidence. These are compact point-in-time detector refs only, not standalone alpha or duplicated upstream model features.',
    updated_at = NOW()
WHERE id = 'cfg_EABAS001';

UPDATE trading_registry
SET note = 'Layer 10 EventRiskGovernor uses the Layer 8 direct-underlying/spot thesis as the canonical intervention target. Layer 9 trading-guidance and option-expression context are optional; crypto/direct-underlying-only routes must not require option context.',
    updated_at = NOW()
WHERE id = 'cfg_ERG002';

UPDATE trading_registry
SET note = 'Layer 7 boundary policy: PositionProjectionModel projects target exposure and holding state; it does not emit buy/sell/hold/open/close/reverse instructions, choose instruments, read option chains, place orders, or mutate broker/account state.',
    updated_at = NOW()
WHERE id = 'cfg_PPVBP001';

UPDATE trading_registry
SET note = 'Accepted conservative Layer 9 V1 DTE policy. DTE is a range tied to Layer 8 holding-time assumptions; V1 avoids 0DTE and extreme short-DTE lottery contracts.',
    updated_at = NOW()
WHERE id = 'cfg_OEDTE001';

UPDATE trading_registry
SET note = 'Accepted Layer 9 V1 moneyness guardrail. Layer 9 uses Layer 8 target range to prevent lottery-like call strikes above coherent bullish target highs and put strikes below coherent bearish target lows. This is still offline model evidence and not broker routing.',
    updated_at = NOW()
WHERE id = 'cfg_OEMG001';

UPDATE trading_registry
SET note = 'Accepted current 9_* OptionExpressionModel scalar score-family tokens for Layer 9. These 10 families separate option-expression eligibility, signed expression direction, contract fit, liquidity fit, IV fit, Greek fit, reward/risk, theta risk, fill quality, and expression confidence.',
    updated_at = NOW()
WHERE id = 'cfg_OEVS001';

UPDATE trading_registry
SET note = 'Layer 8 boundary policy: UnderlyingActionModel produces an offline direct underlying/spot action thesis for stock, ETF, or crypto-style candidates, with optional Layer 9 trading-guidance or option-expression handoff. It must not place broker/exchange orders, emit broker order fields, choose option contracts, or mutate broker/account state.',
    updated_at = NOW()
WHERE id = 'cfg_UAPB001';

UPDATE trading_registry
SET note = 'Reviewed Layer 8 diagnostic field-family tokens for effective exposure calculations, gate decisions, risk-plan attribution, and Layer 9 handoff attribution. Diagnostics are not default scalar score-family rows.',
    updated_at = NOW()
WHERE id = 'cfg_UAPD001';

UPDATE trading_registry
SET note = 'Accepted Layer 8 V1 planned direct-underlying action type vocabulary. maintain means an existing state remains aligned or not worth adjusting; no_trade means no new direct-underlying operation should be initiated.',
    updated_at = NOW()
WHERE id = 'cfg_UAPT001';

UPDATE trading_registry
SET note = 'Reviewed current 8_* resolved plan/handoff field-family tokens for communicating the Layer 8 direct-underlying action thesis to optional Layer 9 trading-guidance or option-expression review and execution-side review. These are not broker order fields.',
    updated_at = NOW()
WHERE id = 'cfg_UAPR001';

UPDATE trading_registry
SET note = 'Accepted UnderlyingActionModel V1 horizons for Layer 8. 390min means one regular US equity session-equivalent horizon measured in tradable minutes; label builders must document same-session vs next-session-close resolution and use purge/embargo controls.',
    updated_at = NOW()
WHERE id = 'cfg_UAVH001';

UPDATE trading_registry
SET note = 'Accepted current 8_* UnderlyingActionModel scalar score-family tokens for Layer 8. These 10 families separate trade eligibility, signed action direction, action intensity, entry quality, expected return, adverse risk, reward/risk, liquidity fit, holding-time fit, and action confidence.',
    updated_at = NOW()
WHERE id = 'cfg_UAVS001';

UPDATE trading_registry
SET note = replace(note, 'Layer 7 ', 'Layer 8 '),
    updated_at = NOW()
WHERE id IN (
  'fld_UAV1001',
  'fld_UAV1003',
  'fld_UAV1004',
  'fld_UAV1006',
  'fld_UAV1007',
  'fld_UAV1008',
  'fld_UAV1009',
  'fld_UAV1010'
);

UPDATE trading_registry
SET note = 'Accepted Layer 10 event-risk governor. It consumes point-in-time residual event evidence with the Layer 8 direct-underlying action thesis as the canonical risk target; optional Layer 9 trading-guidance/option-expression context may be attached when available.',
    updated_at = NOW()
WHERE id = 'trm_ERG001';

UPDATE trading_registry
SET note = 'Accepted Layer 9 model boundary that outputs an optional offline trading-guidance record and optional option-expression context from the Layer 8 direct-underlying thesis. The current V1 option-expression implementation surface is model_09_option_expression.',
    updated_at = NOW()
WHERE id = 'trm_TGM001';

UPDATE trading_registry
SET note = 'Accepted canonical Layer 8 model id. UnderlyingActionModel maps alpha/position state plus point-in-time current/pending underlying exposure, quote/liquidity/borrow state, risk-budget state, and policy gates into an offline direct-underlying action thesis.',
    updated_at = NOW()
WHERE id = 'trm_UAM001';

UPDATE trading_registry
SET note = 'Layer 8 primary offline direct underlying planned action output for stock, ETF, or crypto spot-style candidates. It includes planned action type, effective exposure gap, planned incremental exposure, entry/target/stop/time-horizon rationale, and reason codes; it is not a broker order.',
    updated_at = NOW()
WHERE id = 'trm_UAP001';

UPDATE trading_registry
SET note = 'Layer 8 score/vector output for direct underlying planned action quality by horizon. It carries eligibility, signed action direction, intensity, entry quality, expected return, adverse risk, reward/risk, liquidity fit, holding-time fit, and confidence.',
    updated_at = NOW()
WHERE id = 'trm_UAV001';

UPDATE trading_registry
SET note = 'Layer 8 point-in-time pending direct-underlying order/exposure state input. Pending exposure is adjusted by fill probability to avoid duplicate planned adjustments; it is not a new order instruction.',
    updated_at = NOW()
WHERE id = 'trm_PUOS01';

UPDATE trading_registry
SET note = 'Layer 8 point-in-time underlying quote snapshot reference paired with the option-chain snapshot for moneyness and path replay.',
    updated_at = NOW()
WHERE id = 'trm_UQSR001';

UPDATE trading_registry
SET note = 'Layer 7 PositionProjectionModel output vector for projected target holding state before Layer 8 direct-underlying action planning. It carries target exposure, position gap, utility, cost/risk fit, stability, and projection confidence.',
    updated_at = NOW()
WHERE id = 'trm_TSVEC01';

UPDATE trading_registry
SET note = 'Layer 9 option-expression candidate feature surface using current feature_09 data and model_09 physical names. trading-data derives point-in-time moneyness, spread/liquidity, IV, Greeks, and quality payloads from accepted source_05_option_expression rows; trading-model owns contract ranking and expression choice.',
    updated_at = NOW()
WHERE id = 'dki_OEFS001';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'source_09_event_risk_governor', 'source_10_event_risk_governor'),
    note = replace(note, 'source_09_event_risk_governor', 'source_10_event_risk_governor'),
    updated_at = NOW()
WHERE id IN ('scr_TEHIST001', 'term_TERECENT001', 'term_TERECENT002')
  AND (applies_to LIKE '%source_09_event_risk_governor%' OR note LIKE '%source_09_event_risk_governor%');
