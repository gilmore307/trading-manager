-- Align active registry notes with the completed nine-layer physical renumbering.
-- Historical/applied migration records remain unchanged; this migration updates current registry rows only.

UPDATE trading_registry
SET note = 'Accepted current 9_event_* event-context scalar score-family tokens for model_09_event_risk_governor / Layer 9 EventRiskGovernor. These families separate event presence, timing, intensity, direction bias, alignment, risks, quality, impact scope, scope confidence, escalation risk, and target relevance; enum-like audit fields remain model-local.',
    updated_at = NOW()
WHERE id = 'cfg_ECVS001';

UPDATE trading_registry
SET payload = 'layer_01_proxy_gap_review_required;layer_09_event_adapter_review_required;layer_06_broker_account_route_deferred;layer_07_restriction_account_route_deferred;layer_08_thetadata_terminal_required',
    applies_to = 'trading-execution;realtime_input_coverage;layer_01_market_regime;layer_09_event_risk_governor;model_06_position_projection;model_07_underlying_action;model_08_option_expression;current_physical_names',
    note = 'Current realtime coverage gap summary for the nine-layer stack. Layer 6 broker/account state, Layer 7 restrictions, Layer 8 ThetaData option-chain context, and Layer 9 event adapters remain bounded route gaps until reviewed implementation fills them.',
    updated_at = NOW()
WHERE id = 'cfg_EXEC_RT003';

UPDATE trading_registry
SET note = 'Active layer order accepted on 2026-05-17 and physically aligned on 2026-05-17: Layer 4 is EventFailureRiskModel for agent-accepted event/strategy-failure factors; AlphaConfidence, PositionProjection, UnderlyingAction, TradingGuidance/OptionExpression, and EventRiskGovernor are Layers 5-9. Active script/package/table names use the current nine-layer numbering; historical/applied migration records may retain prior names.',
    updated_at = NOW()
WHERE id = 'cfg_MLRP003';

UPDATE trading_registry
SET note = 'Accepted Layer 8 option-expression evaluation baseline ladder. The current physical score/model namespace uses layer_08/model_08. The model must prove value versus no option, underlying-only expression, naive ATM option, fixed delta/DTE option, and full contract-fit model.',
    updated_at = NOW()
WHERE id = 'cfg_OERB001';

UPDATE trading_registry
SET payload = 'layer_08_after_underlying_action;uses_underlying_action_plan;uses_option_chain_context;no_broker_mutation;model_08_physical_surface',
    note = 'Layer policy for OptionExpressionModel: option expression is Layer 8, consumes Layer 7 underlying path assumptions plus option-chain context, and remains offline without broker mutation. Current physical names use model_08/8_*.',
    updated_at = NOW()
WHERE id = 'cfg_OEML001';

UPDATE trading_registry
SET note = 'Reviewed current 8_* resolved expression field-family tokens for Layer 8 option-expression. They communicate chosen option expression, selected point-in-time contract reference, fit/confidence, and no-option reason codes; they are not broker order fields.',
    updated_at = NOW()
WHERE id = 'cfg_OEPR001';

UPDATE trading_registry
SET note = 'Accepted current 8_* OptionExpressionModel scalar score-family tokens for Layer 8. These 10 families separate option-expression eligibility, signed expression direction, contract fit, liquidity fit, IV fit, Greek fit, reward/risk, theta risk, fill quality, and expression confidence.',
    updated_at = NOW()
WHERE id = 'cfg_OEVS001';

UPDATE trading_registry
SET note = 'Accepted current 6_* PositionProjectionModel scalar score-family tokens for Layer 6 target holding-state projection. These 10 families separate target bias, target exposure, current-position alignment, position gap, utility, cost pressure, risk fit, stability, and projection confidence.',
    updated_at = NOW()
WHERE id = 'cfg_PPVS001';

UPDATE trading_registry
SET note = 'Accepted Layer 7 V1 planned direct-underlying action type vocabulary. maintain means an existing state remains aligned or not worth adjusting; no_trade means no new direct-underlying operation should be initiated.',
    updated_at = NOW()
WHERE id = 'cfg_UAPT001';

UPDATE trading_registry
SET note = 'Reviewed current 7_* resolved plan/handoff field-family tokens for communicating the Layer 7 direct-underlying action thesis to Layer 8 trading guidance and execution-side review. These are not broker order fields.',
    updated_at = NOW()
WHERE id = 'cfg_UAPR001';

UPDATE trading_registry
SET note = 'Accepted current 7_* UnderlyingActionModel scalar score-family tokens for Layer 7. These 10 families separate trade eligibility, signed action direction, action intensity, entry quality, expected return, adverse risk, reward/risk, liquidity fit, holding-time fit, and action confidence.',
    updated_at = NOW()
WHERE id = 'cfg_UAVS001';

UPDATE trading_registry
SET note = replace(note, 'Physical script/model path remains legacy model_05_alpha_confidence until a dedicated renumbering migration.', 'Current physical script/model path is model_05_alpha_confidence.')
WHERE id = 'scr_M5ACGEN';

UPDATE trading_registry
SET note = replace(note, 'Physical script/model path remains legacy model_06_position_projection until a dedicated renumbering migration.', 'Current physical script/model path is model_06_position_projection.')
WHERE id = 'scr_M6PPGEN';

UPDATE trading_registry
SET note = replace(note, 'Physical script/model path remains legacy model_07_underlying_action until a dedicated renumbering migration.', 'Current physical script/model path is model_07_underlying_action.')
WHERE id = 'scr_M7UAGEN';

UPDATE trading_registry
SET note = 'Builds the accepted event-model closeout report: Layer 9 remains a bounded EventRiskGovernor / EventIntelligenceOverlay, broad event alpha and signed earnings/guidance alpha remain blocked, diagnostic artifacts are preserved, and storage deletion stays on hold until reviewed regeneration completes.',
    updated_at = NOW()
WHERE id = 'scr_M8ERGCLS001';

UPDATE trading_registry
SET note = 'Builds the EventRiskGovernor residual-anomaly event discovery artifact from Layers 1-8 base-stack evaluation residuals. The builder searches nearby PIT event families for explanations, observation-pool candidates, and Layer 4 event-failure-risk promotion review packets. It is a registered callable integration surface under the current MODEL_09 physical namespace only: no provider calls, daemon start, model activation, broker/account mutation, destructive SQL, artifact deletion, or automatic event-family promotion.',
    updated_at = NOW()
WHERE id = 'scr_M8ERGRD001';

UPDATE trading_registry
SET note = replace(note, 'using legacy 4_* field tokens', 'using current 5_* field tokens'),
    updated_at = NOW()
WHERE id LIKE 'fld_ACMV%'
  AND note LIKE '%legacy 4_* field tokens%';

UPDATE trading_registry
SET note = replace(replace(note, 'using legacy 5_* field tokens', 'using current 6_* field tokens'), 'Conceptual Layer 6 using', 'Layer 6 using'),
    updated_at = NOW()
WHERE id LIKE 'fld_PPV%'
  AND note LIKE '%legacy 5_* field tokens%';

UPDATE trading_registry
SET note = replace(note, 'Conceptual Layer 6 high-is', 'Layer 7 high-is'),
    updated_at = NOW()
WHERE id LIKE 'fld_UAV%'
  AND note LIKE 'Conceptual Layer 6 high-is%';

UPDATE trading_registry
SET note = replace(replace(replace(note, 'Legacy 8_*', 'Current 8_*'), 'Layer 6 path thesis', 'Layer 7 path thesis'), 'after Layer 6 thesis', 'after Layer 7 thesis'),
    updated_at = NOW()
WHERE id LIKE 'fld_OEV%'
  AND note LIKE 'Legacy 8_*%';

UPDATE trading_registry
SET note = 'Accepted canonical Layer 5 model id. AlphaConfidenceModel builds base/no-event alpha diagnostics from the Layer 1/2/3 state stack, consumes Layer 4 event_failure_risk_vector when applicable, and emits alpha_confidence_vector; current physical surface is model_05_alpha_confidence.',
    updated_at = NOW()
WHERE id = 'trm_ACM001';

UPDATE trading_registry
SET note = 'Layer 5 AlphaConfidenceModel final adjusted output vector with horizon-aware alpha direction, strength, expected residual return, confidence, reliability, path quality, reversal risk, drawdown risk, and alpha-level tradability; current physical surface is model_05_alpha_confidence.',
    updated_at = NOW()
WHERE id = 'trm_ASV001';

UPDATE trading_registry
SET note = 'Accepted dataset-unit policy: Layers 1-2 use one six-month panel; Layers 3-8 use one selected target symbol over one six-month window; Layer 9 EventRiskGovernor is a separate event-risk overlay. Current physical stage tokens use the nine-layer numbering.',
    updated_at = NOW()
WHERE id = 'term_DU001';

UPDATE trading_registry
SET note = 'Accepted current model_06_position_projection physical model-output surface name for Layer 6 PositionProjectionModel position_projection_vector outputs.',
    updated_at = NOW()
WHERE id = 'trm_MTP001';

UPDATE trading_registry
SET note = 'Accepted current model_07_underlying_action physical model-output surface name for Layer 7 UnderlyingActionModel underlying_action_plan and underlying_action_vector outputs.',
    updated_at = NOW()
WHERE id = 'trm_M7UAM01';

UPDATE trading_registry
SET note = 'Accepted current model_08_option_expression model-output surface name for Layer 8 OptionExpressionModel option_expression_plan and expression_vector outputs. This is not live execution.',
    updated_at = NOW()
WHERE id = 'trm_M7OEM01';

UPDATE trading_registry
SET note = 'Accepted current physical model_09_event_risk_governor implementation surface for bounded Layer 9 event-risk evidence and intervention review.',
    updated_at = NOW()
WHERE id = 'trm_M8ERG01';

UPDATE trading_registry
SET note = 'Accepted Layer 8 option-expression model id. OptionExpressionModel consumes Layer 7 underlying path assumptions plus point-in-time option-chain context and emits offline option_expression_plan / expression_vector rows; current physical surface is model_08_option_expression.',
    updated_at = NOW()
WHERE id = 'trm_OEM001';

UPDATE trading_registry
SET note = 'Accepted canonical Layer 6 model id. PositionProjectionModel maps final adjusted alpha confidence plus current/pending position, position-level friction, portfolio exposure, and risk-budget context to projected target holding state; current physical surface is model_06_position_projection.',
    updated_at = NOW()
WHERE id = 'trm_TPM001';

UPDATE trading_registry
SET note = 'Accepted canonical Layer 7 model id. UnderlyingActionModel maps alpha/position state plus point-in-time current/pending underlying exposure, quote/liquidity/borrow state, risk-budget state, and policy gates into an offline direct stock/ETF planned action thesis; current physical surface is model_07_underlying_action.',
    updated_at = NOW()
WHERE id = 'trm_UAM001';
