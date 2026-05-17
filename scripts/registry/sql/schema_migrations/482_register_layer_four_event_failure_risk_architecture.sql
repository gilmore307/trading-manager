-- Register conceptual Layer 04 EventFailureRiskModel architecture insertion.
-- This is a governance/registry migration only. It intentionally preserves current
-- physical script/package/table names until a reviewed code/SQL renumbering migration.

UPDATE trading_registry
SET payload = 'layer_01_market_regime;layer_02_sector_context;layer_03_target_state_vector;layer_04_event_failure_risk;layer_05_alpha_confidence;layer_06_position_projection;layer_07_underlying_action;layer_08_trading_guidance;layer_09_event_risk_governor',
    path = 'trading-model/docs/94_model_stack_closeout.md;trading-model/docs/05_layer_04_event_failure_risk.md;trading-manager/docs/81_decision.md',
    applies_to = 'trading-model;trading-data;trading-manager;model_training_workflow;event_failure_risk_model;event_risk_governor;trading_guidance;legacy_physical_names',
    note = 'Active conceptual layer order accepted on 2026-05-17: Layer 4 is EventFailureRiskModel for agent-accepted event/strategy-failure factors; AlphaConfidence, PositionProjection, UnderlyingAction, TradingGuidance/OptionExpression, and EventRiskGovernor shift to conceptual Layers 5-9. Physical script/package/table names remain legacy until a dedicated code/SQL renumbering migration.'
WHERE id = 'cfg_MLRP003';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
(
  'trm_EFRM001',
  'term',
  'EVENT_FAILURE_RISK_MODEL',
  'text',
  'event_failure_risk_model',
  'trading-model/docs/05_layer_04_event_failure_risk.md',
  'trading-model;event_failure_risk_vector;event_risk_governor;alpha_confidence_model;model_architecture',
  'registry_only',
  'Accepted canonical conceptual Layer 4 model id. EventFailureRiskModel converts agent-accepted event/strategy-failure relationships into pre-alpha failure-risk conditioning; it is not raw event alpha, discovery, action selection, sizing, execution, or broker/account mutation.'
),
(
  'trm_EFRV001',
  'term',
  'EVENT_FAILURE_RISK_VECTOR',
  'text',
  'event_failure_risk_vector',
  'trading-model/docs/05_layer_04_event_failure_risk.md',
  'trading-model;event_failure_risk_model;alpha_confidence_model;event_strategy_promotion_review',
  'registry_only',
  'Conceptual Layer 4 EventFailureRiskModel output vector for reviewed event/strategy-failure conditioning before AlphaConfidenceModel. It carries failure-risk, block/cap/disable pressure, path-risk amplification, evidence quality, applicability confidence, and reason refs; it is not standalone directional alpha or an order instruction.'
),
(
  'cfg_EFRB001',
  'config',
  'EVENT_FAILURE_RISK_BOUNDARY_POLICY',
  'text',
  'reviewed_event_strategy_failure_evidence_only;no_raw_event_alpha;no_unreviewed_family_auto_promotion;no_buy_sell_hold;no_position_sizing;no_option_expression;no_broker_mutation;no_destructive_sql',
  'trading-model/docs/05_layer_04_event_failure_risk.md',
  'event_failure_risk_model;event_failure_risk_vector;alpha_confidence_model;event_risk_governor;model_architecture',
  'registry_only',
  'Layer 4 boundary policy: EventFailureRiskModel accepts only agent-reviewed event/strategy-failure factors and outputs conditioning for Layer 5 AlphaConfidenceModel. EventRiskGovernor may propose promotions, but no family enters Layer 4 without evidence packet plus agent review.'
),
(
  'cfg_EFRS001',
  'config',
  'EVENT_FAILURE_RISK_VECTOR_SCORE_FAMILIES',
  'text',
  '4_event_strategy_failure_risk_score_<horizon>;4_event_entry_block_pressure_score_<horizon>;4_event_exposure_cap_pressure_score_<horizon>;4_event_strategy_disable_pressure_score_<horizon>;4_event_path_risk_amplifier_score_<horizon>;4_event_evidence_quality_score_<horizon>;4_event_applicability_confidence_score_<horizon>',
  'trading-model/docs/05_layer_04_event_failure_risk.md',
  'event_failure_risk_model;event_failure_risk_vector;state_vector_value;alpha_confidence_model',
  'registry_only',
  'Accepted conceptual Layer 4 event-failure-risk score-family namespace. These score families require reviewed evidence and are pre-alpha failure-risk conditioning only; they do not authorize standalone event alpha, action selection, sizing, execution, or broker/account mutation.'
),
(
  'cfg_EFRH001',
  'config',
  'EVENT_FAILURE_RISK_VECTOR_HORIZONS',
  'text',
  '5min;15min;60min;390min',
  'trading-model/docs/05_layer_04_event_failure_risk.md',
  'event_failure_risk_model;event_failure_risk_vector;alpha_confidence_model',
  'registry_only',
  'Accepted EventFailureRiskModel V1 horizons aligned with downstream alpha/position/action horizons. 390min means one regular US equity session-equivalent horizon measured in tradable minutes.'
),
(
  'cfg_EFRP001',
  'config',
  'EVENT_FAMILY_TO_LAYER_04_PROMOTION_POLICY',
  'text',
  'script_emitted_evidence_packet_required;matched_controls_required;split_stability_required;pit_leakage_review_required;incremental_value_over_base_stack_required;agent_review_required;manager_decision_required;no_automatic_promotion',
  'trading-model/docs/05_layer_04_event_failure_risk.md;trading-model/docs/100_event_family_scouting.md;trading-manager/docs/81_decision.md',
  'event_risk_governor;event_family_strategy_promotion_review;event_failure_risk_model;manager_decision',
  'registry_only',
  'Promotion policy from Layer 9 EventRiskGovernor research into Layer 4 EventFailureRiskModel. Residual/event discovery may generate hypotheses and review packets, but cannot automatically promote event families into front decision scope.'
)
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();

-- Keep registry paths aligned with renamed docs while preserving legacy physical implementation names.
UPDATE trading_registry
SET path = replace(path, 'trading-model/docs/05_layer_04_alpha_confidence.md', 'trading-model/docs/06_layer_05_alpha_confidence.md')
WHERE path LIKE '%trading-model/docs/05_layer_04_alpha_confidence.md%';

UPDATE trading_registry
SET path = replace(path, 'trading-model/docs/06_layer_05_position_projection.md', 'trading-model/docs/07_layer_06_position_projection.md')
WHERE path LIKE '%trading-model/docs/06_layer_05_position_projection.md%';

UPDATE trading_registry
SET path = replace(path, 'trading-model/docs/07_layer_06_underlying_action.md', 'trading-model/docs/08_layer_07_underlying_action.md')
WHERE path LIKE '%trading-model/docs/07_layer_06_underlying_action.md%';

UPDATE trading_registry
SET path = replace(path, 'trading-model/docs/08_layer_07_trading_guidance.md', 'trading-model/docs/09_layer_08_trading_guidance.md')
WHERE path LIKE '%trading-model/docs/08_layer_07_trading_guidance.md%';

UPDATE trading_registry
SET path = replace(path, 'trading-model/docs/09_layer_08_event_risk_governor.md', 'trading-model/docs/10_layer_09_event_risk_governor.md')
WHERE path LIKE '%trading-model/docs/09_layer_08_event_risk_governor.md%';

UPDATE trading_registry
SET note = 'After the 2026-05-17 conceptual reorder, physical script/table/package/stage names may temporarily retain legacy numbering. Active docs must distinguish conceptual layer order from legacy implementation names until a reviewed migration renames code and SQL surfaces.',
    applies_to = 'model_04_alpha_confidence;model_05_position_projection;model_06_underlying_action;model_07_option_expression;model_08_event_risk_governor;event_failure_risk_model;layer_04_event_failure_risk;legacy_physical_names;model_architecture'
WHERE id = 'cfg_LPNM001';

UPDATE trading_registry
SET note = 'Accepted canonical conceptual Layer 5 model id. AlphaConfidenceModel builds base/no-event alpha diagnostics from the Layer 1/2/3 state stack, consumes Layer 4 event_failure_risk_vector when applicable, and emits alpha_confidence_vector; current physical surface remains model_04_alpha_confidence until renumbering.',
    applies_to = 'trading-model;market_context_state;sector_context_state;target_context_state;event_failure_risk_vector;model_04_alpha_confidence;alpha_confidence_vector;legacy_physical_names'
WHERE id = 'trm_ACM001';

UPDATE trading_registry
SET note = 'Conceptual Layer 5 AlphaConfidenceModel final adjusted output vector with horizon-aware alpha direction, strength, expected residual return, confidence, reliability, path quality, reversal risk, drawdown risk, and alpha-level tradability; current physical surface remains model_04_alpha_confidence until renumbering.',
    applies_to = 'trading-model;alpha_confidence_model;model_04_alpha_confidence;market_context_state;sector_context_state;target_context_state;event_failure_risk_vector;legacy_physical_names'
WHERE id = 'trm_ASV001';

UPDATE trading_registry
SET note = 'Accepted current physical model_04_alpha_confidence model-output surface name for conceptual Layer 5 AlphaConfidenceModel final adjusted alpha_confidence_vector outputs. Base/no-event alpha fields are diagnostics, not the default downstream surface.',
    path = 'trading-model/docs/06_layer_05_alpha_confidence.md',
    applies_to = 'trading-model;alpha_confidence_model;market_context_state;sector_context_state;target_context_state;event_failure_risk_vector;alpha_confidence_vector;legacy_physical_names'
WHERE id = 'trm_MAC001';

UPDATE trading_registry
SET note = 'Accepted canonical conceptual Layer 6 model id. PositionProjectionModel maps final adjusted alpha confidence plus current/pending position, position-level friction, portfolio exposure, and risk-budget context to projected target holding state; current physical surface remains model_05_position_projection until renumbering.',
    path = 'trading-model/docs/07_layer_06_position_projection.md'
WHERE id = 'trm_TPM001';

UPDATE trading_registry
SET note = 'Conceptual Layer 6 PositionProjectionModel output vector for projected target holding state before conceptual Layer 7 direct-underlying action planning. It carries target exposure, position gap, utility, cost/risk fit, stability, and projection confidence; it is not an order instruction, planned action, option expression, or final action.',
    path = 'trading-model/docs/07_layer_06_position_projection.md'
WHERE id = 'trm_TSVEC01';

UPDATE trading_registry
SET note = 'Accepted canonical conceptual Layer 7 model id. UnderlyingActionModel maps alpha/position state plus point-in-time current/pending underlying exposure, quote/liquidity/borrow state, risk-budget state, and policy gates into an offline direct stock/ETF planned action thesis; current physical surface remains model_06_underlying_action until renumbering.',
    path = 'trading-model/docs/08_layer_07_underlying_action.md'
WHERE id = 'trm_UAM001';

UPDATE trading_registry
SET note = 'Conceptual Layer 7 primary offline direct stock/ETF planned action output. It includes planned action type, effective exposure gap, planned incremental exposure, entry/target/stop/time-stop thesis, risk plan, conceptual Layer 8 trading-guidance handoff, and reason codes; it is not a broker order, final order quantity, option contract, or execution instruction.',
    path = 'trading-model/docs/08_layer_07_underlying_action.md'
WHERE id = 'trm_UAP001';

UPDATE trading_registry
SET note = 'Conceptual Layer 7 score/vector output for direct stock/ETF planned action quality by horizon. It carries eligibility, signed action direction, intensity, entry quality, expected return, adverse risk, reward/risk, liquidity fit, holding-time fit, and action confidence; it is not a broker order or option-expression vector.',
    path = 'trading-model/docs/08_layer_07_underlying_action.md'
WHERE id = 'trm_UAV001';

UPDATE trading_registry
SET note = 'Accepted conceptual Layer 8 option-expression model id. OptionExpressionModel consumes Layer 7 underlying path assumptions plus point-in-time option-chain context and emits offline option_expression_plan / expression_vector rows; current physical surface remains model_07_option_expression until renumbering.',
    path = 'trading-model/docs/09_layer_08_trading_guidance.md'
WHERE id = 'trm_OEM001';

UPDATE trading_registry
SET note = 'Conceptual Layer 8 primary offline option-expression output. It includes selected expression type, selected option right, point-in-time selected contract reference, contract constraints, premium-risk plan, underlying thesis reference, reason codes, and diagnostics; it is not a broker order or account mutation.',
    path = 'trading-model/docs/09_layer_08_trading_guidance.md'
WHERE id = 'trm_OEP001';

UPDATE trading_registry
SET note = 'Accepted conceptual Layer 9 event-risk governor. It consumes point-in-time residual event evidence after base Layer 8 trading guidance, may warn/block/cap/review or emit promotion packets, and remains bounded to risk governance unless reviewed evidence moves a family into Layer 4 EventFailureRiskModel.',
    path = 'trading-model/docs/10_layer_09_event_risk_governor.md',
    applies_to = 'trading-model;trading-data;source_08_event_risk_governor;model_08_event_risk_governor;event_context_vector;event_risk_intervention;event_failure_risk_model;legacy_physical_names'
WHERE id = 'trm_ERG001';

UPDATE trading_registry
SET note = 'Accepted current physical model_08_event_risk_governor implementation surface for bounded conceptual Layer 9 event-risk evidence and intervention review. Physical name remains legacy until a dedicated renumbering migration.',
    path = 'trading-model/docs/10_layer_09_event_risk_governor.md'
WHERE id = 'trm_M8ERG01';
