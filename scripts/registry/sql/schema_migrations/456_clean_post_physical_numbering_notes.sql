-- Clean active registry labels/notes after the current physical numbering migration.
-- Historical migrations and reviewed artifacts intentionally remain unchanged.

UPDATE trading_registry
SET key = replace(key, 'LAYER_08_OPTION_BUCKET', 'LAYER_07_OPTION_BUCKET'),
    updated_at = NOW()
WHERE id IN ('cfg_L8OPT001', 'cfg_L8OPT002', 'cfg_L8OPT003')
  AND key LIKE 'LAYER_08_OPTION_BUCKET%';

UPDATE trading_registry
SET note = 'Layer 7 option-expression contract bucket expansion scans listed expirations from near to far for the option-expression boundary.',
    updated_at = NOW()
WHERE id = 'cfg_L8OPT001';

UPDATE trading_registry
SET note = 'Layer 7 option-expression bucket strikes cover the current-price to target-price listed-strike corridor plus three actual listed strike levels on each side.',
    updated_at = NOW()
WHERE id = 'cfg_L8OPT002';

UPDATE trading_registry
SET note = 'Layer 7 option-expression historical model-construction buckets intentionally retain extreme/illiquid contracts for robustness instead of filtering them out at acquisition time.',
    updated_at = NOW()
WHERE id = 'cfg_L8OPT003';

UPDATE trading_registry
SET note = 'Layer 7 option-expression V1 coverage is single-leg only: long call, long put, or no-option expression. Multi-leg spreads are deferred beyond V1.',
    updated_at = NOW()
WHERE id = 'cfg_L8OPT004';

UPDATE trading_registry
SET note = 'Canonical model ids accepted by the unified manager-side promotion review request planner, ordered by current conceptual and physical layer order.',
    updated_at = NOW()
WHERE key = 'MODEL_PROMOTION_UNIFIED_TARGETS';

UPDATE trading_registry
SET note = 'Reviewed position-projection handoff summary field-family tokens for communicating resolved target holding state from Layer 5 PositionProjectionModel to Layer 6 UnderlyingActionModel. These are not buy/sell/hold, planned quantities, order instructions, or option-expression fields.',
    updated_at = NOW()
WHERE key = 'POSITION_PROJECTION_HANDOFF_SUMMARY_FIELD_FAMILIES';

UPDATE trading_registry
SET note = 'Accepted Layer 5 PositionProjectionModel scalar score-family tokens for target holding-state projection. These 10 families separate target bias, target exposure, current-position alignment, position gap, utility, cost pressure, risk fit, stability, and projection confidence.',
    updated_at = NOW()
WHERE key = 'POSITION_PROJECTION_VECTOR_SCORE_FAMILIES';

UPDATE trading_registry
SET note = 'Reviewed Layer 6 resolved plan/handoff field-family tokens for communicating the direct-underlying action thesis to Layer 7 trading guidance and execution-side review. These are not broker order fields.',
    updated_at = NOW()
WHERE key = 'UNDERLYING_ACTION_RESOLVED_FIELD_FAMILIES';

UPDATE trading_registry
SET note = 'Accepted Layer 6 UnderlyingActionModel scalar score-family tokens. These 10 families separate trade eligibility, signed action direction, action intensity, entry quality, expected return, adverse risk, reward/risk, liquidity fit, holding-time fit, and action confidence.',
    updated_at = NOW()
WHERE key = 'UNDERLYING_ACTION_VECTOR_SCORE_FAMILIES';

UPDATE trading_registry
SET note = 'Layer 7 option-expression candidate feature surface. trading-data derives point-in-time moneyness, spread/liquidity, IV, Greeks, and quality payloads from accepted source_05_option_expression rows; trading-model owns contract ranking and expression choice.',
    updated_at = NOW()
WHERE key = 'FEATURE_07_OPTION_EXPRESSION';

UPDATE trading_registry
SET note = 'Layer 8 EventRiskGovernor feature surface. trading-data derives point-in-time event-category, scope, dedup, source-priority, and quality payloads from accepted source_08_event_risk_governor rows; trading-model owns final event-risk context/intervention construction.',
    updated_at = NOW()
WHERE key = 'FEATURE_08_EVENT_RISK_GOVERNOR';

UPDATE trading_registry
SET note = 'Stable callable entrypoint for generating deterministic Layer 4 AlphaConfidenceModel alpha_confidence_vector rows.',
    updated_at = NOW()
WHERE key = 'MODEL_04_ALPHA_CONFIDENCE_GENERATE';

UPDATE trading_registry
SET note = 'Stable callable entrypoint for generating deterministic Layer 5 PositionProjectionModel position_projection_vector rows.',
    updated_at = NOW()
WHERE key = 'MODEL_05_POSITION_PROJECTION_GENERATE';

UPDATE trading_registry
SET note = 'Stable callable entrypoint for generating deterministic Layer 6 UnderlyingActionModel underlying_action_plan rows.',
    updated_at = NOW()
WHERE key = 'MODEL_06_UNDERLYING_ACTION_GENERATE';

UPDATE trading_registry
SET note = 'Stable callable entrypoint for generating deterministic Layer 7 OptionExpressionModel option_expression_plan rows.',
    updated_at = NOW()
WHERE key = 'MODEL_07_OPTION_EXPRESSION_GENERATE';
