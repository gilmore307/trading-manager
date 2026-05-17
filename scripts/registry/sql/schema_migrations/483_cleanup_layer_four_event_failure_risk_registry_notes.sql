-- Clean up registry notes after conceptual Layer 04 EventFailureRiskModel insertion.
-- Governance/registry text only; physical package/script/table names remain legacy.

UPDATE trading_registry
SET applies_to = replace(applies_to, 'layers_1_8', 'layers_1_9'),
    note = replace(note, 'accepted eight-layer map', 'accepted nine-layer conceptual map'),
    updated_at = NOW()
WHERE applies_to LIKE '%layers_1_8%'
   OR note LIKE '%accepted eight-layer map%';

UPDATE trading_registry
SET payload = replace(
        replace(payload, 'layers_03_07_target_symbol_six_month', 'layers_03_08_target_symbol_six_month'),
        'layer_08_event_risk_governor_six_month_overlay',
        'layer_09_event_risk_governor_six_month_overlay'
    ),
    note = 'Accepted dataset-unit policy: Layers 1-2 use one six-month panel; conceptual Layers 3-8 use one selected target symbol over one six-month window; conceptual Layer 9 EventRiskGovernor is a separate event-risk overlay. Physical stage tokens remain legacy until a dedicated renumbering migration.',
    updated_at = NOW()
WHERE id = 'term_DU001';

UPDATE trading_registry
SET payload = 'layer_01_background_panel_six_month_unit;layer_02_sector_panel_six_month_unit;layers_03_08_target_symbol_six_month_unit;legacy_layer_07_option_expression_after_target_chain_complete;selected_target_symbol_required_for_layer_03_plus;reviewed_exception_required_for_target_fanout',
    applies_to = 'manager_model_training_workflow_plan;historical_training;scheduler;dataset_expansion;layer_01_market_regime;layer_02_sector_context;layer_03_target_state_vector;layer_04_event_failure_risk;model_04_alpha_confidence;model_05_position_projection;model_06_underlying_action;model_07_option_expression;model_08_event_risk_governor;legacy_physical_names',
    note = 'Formal workflow progression is segmented by dataset unit: Layers 1-2 use one six-month panel; conceptual Layers 3-8 run one selected target symbol over one six-month unit; conceptual Layer 9 EventRiskGovernor is a separate event-risk overlay. Physical layer_07_option_expression remains the legacy option-expression stage token.',
    updated_at = NOW()
WHERE id = 'cfg_MWFP002';

UPDATE trading_registry
SET note = 'Owner-facing model layer readiness summary for the accepted nine-layer conceptual map, parameters, versions, metrics, blockers, legacy physical-name caveats, and promotion posture.',
    updated_at = NOW()
WHERE id = 'art_DASHRM005';

UPDATE trading_registry
SET note = 'Accepted legacy 8_* event-context scalar score-family tokens for legacy model_08_event_risk_governor / conceptual Layer 9 EventRiskGovernor. These families separate event presence, timing, intensity, direction bias, alignment, risks, quality, impact scope, scope confidence, escalation risk, and target relevance; enum-like audit fields remain model-local.',
    updated_at = NOW()
WHERE id = 'cfg_ECVS001';

UPDATE trading_registry
SET note = replace(note, 'Layer 7 option-expression', 'conceptual Layer 8 option-expression'),
    updated_at = NOW()
WHERE id IN ('cfg_L8OPT001','cfg_L8OPT002','cfg_L8OPT003','cfg_L8OPT004','cfg_OERB001','cfg_OEPB001','cfg_OEPR001','cfg_OEPT001','cfg_OEVS001','trm_EXV001','term_L8GATE001','dki_OEFS001','scr_L8FEAT001','scr_L8GATE001')
  AND note LIKE '%Layer 7 option-expression%';

UPDATE trading_registry
SET note = replace(note, 'Conceptual Layer 7', 'Conceptual Layer 8'),
    updated_at = NOW()
WHERE id IN ('cfg_OEPB001','cfg_OEVS001','trm_EXV001')
  AND note LIKE '%Conceptual Layer 7%';

UPDATE trading_registry
SET note = replace(note, 'conceptual Layer 7', 'conceptual Layer 8'),
    updated_at = NOW()
WHERE id IN ('cfg_OEPR001','cfg_OEPT001','term_L8GATE001','scr_L8FEAT001','scr_L8GATE001')
  AND note LIKE '%conceptual Layer 7%';

UPDATE trading_registry
SET note = 'Accepted conceptual Layer 8 option-expression evaluation baseline ladder. The current physical score/model namespace remains legacy layer_07/model_07 until a dedicated renumbering migration. The model must prove value versus no option, underlying-only expression, naive ATM option, fixed delta/DTE option, and full contract-fit model.',
    updated_at = NOW()
WHERE id = 'cfg_OERB001';

UPDATE trading_registry
SET note = 'Conceptual Layer 8 option-expression boundary policy: OptionExpressionModel produces an offline option-expression plan and expression vector. Physical model_07/7_* names remain legacy. It must not place orders, emit broker order fields, choose route/time-in-force, emit final order quantity, mutate broker/account state, create maintain/no-trade overlays in V1, use 0DTE in V1, use adjusted contracts in V1, select contracts outside the preferred delta policy, or select strikes outside coherent underlying-action target-range guardrails.',
    updated_at = NOW()
WHERE id = 'cfg_OEPB001';

UPDATE trading_registry
SET note = 'Reviewed legacy 7_* resolved expression field-family tokens for conceptual Layer 8 option-expression. They communicate chosen option expression, selected point-in-time contract reference, fit/confidence, and no-option reason codes; they are not broker order fields.',
    updated_at = NOW()
WHERE id = 'cfg_OEPR001';

UPDATE trading_registry
SET note = 'Accepted conceptual Layer 8 V1 option-expression type vocabulary. Current physical model_07/7_* names remain legacy. V1 supports single-leg long call, single-leg long put, and no-option-expression outcomes only.',
    updated_at = NOW()
WHERE id = 'cfg_OEPT001';

UPDATE trading_registry
SET note = 'Accepted legacy 7_* OptionExpressionModel scalar score-family tokens for conceptual Layer 8. These 10 families separate option-expression eligibility, signed expression direction, contract fit, liquidity fit, IV fit, Greek fit, reward/risk, theta risk, fill quality, and expression confidence.',
    updated_at = NOW()
WHERE id = 'cfg_OEVS001';

UPDATE trading_registry
SET note = 'Reviewed position-projection handoff summary field-family tokens for communicating resolved target holding state from conceptual Layer 6 PositionProjectionModel to conceptual Layer 7 UnderlyingActionModel. Physical 5_* / model_05 names remain legacy. These are not buy/sell/hold, planned quantities, order instructions, or option-expression fields.',
    updated_at = NOW()
WHERE id = 'cfg_PPVHS001';

UPDATE trading_registry
SET note = 'Accepted legacy 5_* PositionProjectionModel scalar score-family tokens for conceptual Layer 6 target holding-state projection. These 10 families separate target bias, target exposure, current-position alignment, position gap, utility, cost pressure, risk fit, stability, and projection confidence.',
    updated_at = NOW()
WHERE id = 'cfg_PPVS001';

UPDATE trading_registry
SET note = 'Reviewed legacy 6_* resolved plan/handoff field-family tokens for communicating the conceptual Layer 7 direct-underlying action thesis to conceptual Layer 8 trading guidance and execution-side review. These are not broker order fields.',
    updated_at = NOW()
WHERE id = 'cfg_UAPR001';

UPDATE trading_registry
SET note = 'Accepted legacy 6_* UnderlyingActionModel scalar score-family tokens for conceptual Layer 7. These 10 families separate trade eligibility, signed action direction, action intensity, entry quality, expected return, adverse risk, reward/risk, liquidity fit, holding-time fit, and action confidence.',
    updated_at = NOW()
WHERE id = 'cfg_UAVS001';

UPDATE trading_registry
SET note = 'Canonical price-action event tokens for legacy model_08_event_risk_governor / conceptual Layer 9 EventRiskGovernor. They describe board/tape behavior used as event-risk evidence, not buy/sell/hold decisions or execution instructions.',
    updated_at = NOW()
WHERE id = 'cfg_PAE001';

UPDATE trading_registry
SET note = 'Conceptual Layer 8 option-expression candidate feature surface using legacy feature_07/model_07 physical names. trading-data derives point-in-time moneyness, spread/liquidity, IV, Greeks, and quality payloads from accepted source_05_option_expression rows; trading-model owns contract ranking and expression choice.',
    updated_at = NOW()
WHERE id = 'dki_OEFS001';

UPDATE trading_registry
SET note = 'Legacy feature_08_event_risk_governor feature surface for conceptual Layer 9 EventRiskGovernor. trading-data derives point-in-time event-category, scope, dedup, source-priority, and quality payloads from accepted source_08_event_risk_governor rows; trading-model owns final event-risk context/intervention construction.',
    updated_at = NOW()
WHERE id = 'dki_EOFS001';

UPDATE trading_registry
SET note = 'Manager-owned legacy layer_07_option_expression feature-stage adapter for conceptual Layer 8 option-expression. It writes a first-class no-provider/no-feature skip receipt when the reviewed gate has zero active target chains, or delegates to trading-data feature_07 option-expression generation after approved active-path acquisition.',
    updated_at = NOW()
WHERE id = 'scr_L8FEAT001';

UPDATE trading_registry
SET note = 'Manager-owned review for legacy layer_07_option_expression acquisition at the conceptual Layer 8 option-expression boundary. Active target chains are prepared for autonomous option-snapshot acquisition; no manual provider gate is required.',
    updated_at = NOW()
WHERE id IN ('scr_L8GATE001','term_L8GATE001');

UPDATE trading_registry
SET note = 'Stable callable entrypoint for generating deterministic conceptual Layer 5 AlphaConfidenceModel alpha_confidence_vector rows. Physical script/model path remains legacy model_04_alpha_confidence until a dedicated renumbering migration.',
    applies_to = 'trading-model;alpha_confidence_model;model_04_alpha_confidence;alpha_confidence_vector;target_context_state;event_failure_risk_vector;legacy_physical_names',
    updated_at = NOW()
WHERE id = 'scr_M5ACGEN';

UPDATE trading_registry
SET note = 'Stable callable entrypoint for generating deterministic conceptual Layer 6 PositionProjectionModel position_projection_vector rows. Physical script/model path remains legacy model_05_position_projection until a dedicated renumbering migration.',
    updated_at = NOW()
WHERE id = 'scr_M6PPGEN';

UPDATE trading_registry
SET note = 'Stable callable entrypoint for generating deterministic conceptual Layer 7 UnderlyingActionModel underlying_action_plan rows. Physical script/model path remains legacy model_06_underlying_action until a dedicated renumbering migration.',
    updated_at = NOW()
WHERE id = 'scr_M7UAGEN';

UPDATE trading_registry
SET note = 'Builds the non-mutating fine-grained event-family batch catalog for legacy model_08_event_risk_governor / conceptual Layer 9 EventRiskGovernor association scouting. Routing buckets such as symbol_news, sector_news, macro_news, sec_filing, and earnings_guidance are split into mechanism-level first-pass family packets, a priority queue, and blocker queue before any price/path association study, risk promotion, or alpha claim. The helper performs no provider calls, model activation, broker/account mutation, or artifact deletion.',
    updated_at = NOW()
WHERE id = 'scr_M8ERGFAM001';

UPDATE trading_registry
SET note = 'Stable callable entrypoint for generating deterministic legacy model_08_event_risk_governor / conceptual Layer 9 EventRiskGovernor event-risk context/intervention rows from local/fixture event-risk input evidence.',
    updated_at = NOW()
WHERE id = 'scr_M8ERGGEN';

UPDATE trading_registry
SET note = replace(note, 'Conceptual Layer 4 AlphaConfidence', 'Conceptual Layer 5 AlphaConfidence using legacy 4_* field tokens'),
    applies_to = replace(applies_to, 'event_context_vector', 'event_failure_risk_vector'),
    updated_at = NOW()
WHERE id LIKE 'fld_ACMV%'
  AND note LIKE '%Conceptual Layer 4 AlphaConfidence%';

UPDATE trading_registry
SET note = replace(note, 'Conceptual Layer 5', 'Conceptual Layer 6 using legacy 5_* field tokens'),
    updated_at = NOW()
WHERE id LIKE 'fld_PPV%'
  AND note LIKE '%Conceptual Layer 5%';

UPDATE trading_registry
SET note = replace(note, 'Layer 8 EventRiskGovernor', 'legacy model_08_event_risk_governor / conceptual Layer 9 EventRiskGovernor'),
    updated_at = NOW()
WHERE id LIKE 'fld_EOMV%'
  AND note LIKE '%Layer 8 EventRiskGovernor%';

UPDATE trading_registry
SET note = replace(note, 'conceptual Layer 7 option-expression', 'conceptual Layer 8 option-expression'),
    updated_at = NOW()
WHERE id LIKE 'fld_OEV%'
  AND note LIKE '%conceptual Layer 7 option-expression%';

UPDATE trading_registry
SET note = replace(note, 'Conceptual Layer 4 alpha confidence', 'conceptual Layer 5 alpha confidence'),
    updated_at = NOW()
WHERE id LIKE 'fld_PPV%'
  AND note LIKE '%Conceptual Layer 4 alpha confidence%';

UPDATE trading_registry
SET note = 'Accepted current model_05_position_projection physical model-output surface name for conceptual Layer 6 PositionProjectionModel position_projection_vector outputs. Physical name remains legacy until a dedicated renumbering migration.',
    updated_at = NOW()
WHERE id = 'trm_MTP001';

UPDATE trading_registry
SET note = 'Accepted current model_06_underlying_action physical model-output surface name for conceptual Layer 7 UnderlyingActionModel underlying_action_plan and underlying_action_vector outputs. Physical name remains legacy until a dedicated renumbering migration.',
    updated_at = NOW()
WHERE id = 'trm_M7UAM01';
