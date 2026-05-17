-- Clean active registry rows that still carried stale legacy/conceptual wording after the nine-layer physical alignment.
-- This migration updates current registry rows only; historical/applied migration records remain unchanged.

UPDATE trading_registry
SET note = 'Accepted current 5_* AlphaConfidenceModel scalar score-family tokens for Layer 5. These 9 families separate alpha direction, strength, expected residual return, confidence, reliability, path quality, reversal risk, drawdown risk, and alpha-level tradability.',
    updated_at = NOW()
WHERE id = 'cfg_ACVS001';

UPDATE trading_registry
SET payload = replace(payload, 'legacy_layer_08_option_expression_after_target_chain_complete', 'layer_08_option_expression_after_target_chain_complete'),
    note = 'Formal workflow progression is segmented by dataset unit: Layers 1-2 use one six-month panel; Layers 3-8 run one selected target symbol over one six-month unit; Layer 9 EventRiskGovernor is a separate event-risk overlay. Current layer_08_option_expression remains the option-expression stage token.',
    updated_at = NOW()
WHERE id = 'cfg_MWFP002';

UPDATE trading_registry
SET note = 'Accepted Layer 8 V1 option-expression type vocabulary. Current physical model_08/8_* names are active. V1 supports single-leg long call, single-leg long put, and no-option-expression outcomes only.',
    updated_at = NOW()
WHERE id = 'cfg_OEPT001';

UPDATE trading_registry
SET note = 'Accepted UnderlyingActionModel V1 horizons for Layer 7. 390min means one regular US equity session-equivalent horizon measured in tradable minutes; label builders must document same-session vs next-session-close resolution and use purge/embargo controls.',
    updated_at = NOW()
WHERE id = 'cfg_UAVH001';

UPDATE trading_registry
SET payload = replace(payload, 'conceptual Layer 8', 'Layer 8'),
    note = replace(note, 'conceptual Layer 8', 'Layer 8'),
    updated_at = NOW()
WHERE id LIKE 'cfg_L8OPT%';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'manager_layer_eight_event_risk_governor_input_materialization', 'manager_layer_nine_event_risk_governor_input_materialization'),
    note = 'Summary field reporting requested-window row counts by required event feed source for the current layer_09_event_risk_governor / Layer 9 coverage gate.',
    updated_at = NOW()
WHERE id = 'fld_L4EVTCOV002';

UPDATE trading_registry
SET note = 'Manager-owned current layer_08_option_expression feature-stage adapter for Layer 8 option-expression. It writes a first-class no-provider/no-feature skip receipt when the reviewed gate has zero active target chains, or delegates to trading-data feature_08 option-expression generation after approved active-path acquisition.',
    updated_at = NOW()
WHERE id = 'scr_L8FEAT001';

UPDATE trading_registry
SET note = replace(note, 'conceptual Layer 8', 'Layer 8'),
    updated_at = NOW()
WHERE id IN ('scr_L8GATE001', 'term_L8GATE001');

UPDATE trading_registry
SET note = replace(replace(note, 'Conceptual Layer 6', 'Layer 6'), 'conceptual Layer 5', 'Layer 5'),
    updated_at = NOW()
WHERE id IN ('cfg_PPVBP001', 'cfg_PPVHS001', 'trm_TSVEC01');

UPDATE trading_registry
SET note = replace(note, 'Conceptual Layer 7', 'Layer 7'),
    updated_at = NOW()
WHERE id IN ('cfg_UAPB001', 'trm_UAP001');

UPDATE trading_registry
SET note = replace(note, 'conceptual Layer 9', 'Layer 9'),
    updated_at = NOW()
WHERE id IN ('cfg_APRW001', 'cfg_EABL001', 'cfg_ERIS001', 'cfg_PAE002', 'cfg_PAE001', 'dki_EOFS001', 'scr_M8ERGFAM001', 'scr_M8ERGGEN', 'trm_EFRM001', 'trm_ERG001')
   OR id LIKE 'fld_EOMV%';

UPDATE trading_registry
SET note = replace(replace(replace(note,
      'conceptual Layer 8', 'Layer 8'),
      'conceptual Layer 7', 'Layer 7'),
      'Conceptual Layer 8', 'Layer 8'),
    updated_at = NOW()
WHERE id LIKE 'fld_OEV%';
