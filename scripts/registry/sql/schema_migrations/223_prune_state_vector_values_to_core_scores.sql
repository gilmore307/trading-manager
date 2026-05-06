-- Keep registry state_vector_value rows limited to core model score tokens.
-- Diagnostics, routing/audit fields, state-vector block/group names, windows,
-- enum values, research payloads, and unresolved source-mapping placeholders stay
-- in model-local docs/contracts unless later promoted through a manager-phase
-- durable interface review.

WITH core_scores(key) AS (
  VALUES
    -- Layer 1 MarketRegime core scores.
    ('BREADTH_PARTICIPATION_SCORE'),
    ('CORRELATION_CROWDING_SCORE'),
    ('DISPERSION_OPPORTUNITY_SCORE'),
    ('MARKET_DIRECTION_SCORE'),
    ('MARKET_DIRECTION_STRENGTH_SCORE'),
    ('MARKET_LIQUIDITY_PRESSURE_SCORE'),
    ('MARKET_LIQUIDITY_SUPPORT_SCORE'),
    ('MARKET_RISK_STRESS_SCORE'),
    ('MARKET_STABILITY_SCORE'),
    ('MARKET_TRANSITION_RISK_SCORE'),
    ('MARKET_TREND_QUALITY_SCORE'),

    -- Layer 2 SectorContext core scores.
    ('MARKET_CONTEXT_SUPPORT_SCORE'),
    ('SECTOR_BREADTH_CONFIRMATION_SCORE'),
    ('SECTOR_CROWDING_RISK_SCORE'),
    ('SECTOR_INTERNAL_DISPERSION_SCORE'),
    ('SECTOR_LIQUIDITY_TRADABILITY_SCORE'),
    ('SECTOR_RELATIVE_DIRECTION_SCORE'),
    ('SECTOR_TRADABILITY_SCORE'),
    ('SECTOR_TRANSITION_RISK_SCORE'),
    ('SECTOR_TREND_QUALITY_SCORE'),
    ('SECTOR_TREND_STABILITY_SCORE'),

    -- Layer 3 TargetStateVector core score families.
    ('CONTEXT_DIRECTION_ALIGNMENT_SCORE_BY_WINDOW'),
    ('CONTEXT_SUPPORT_QUALITY_SCORE_BY_WINDOW'),
    ('TARGET_DIRECTION_SCORE_BY_WINDOW'),
    ('TARGET_DIRECTION_STRENGTH_SCORE_BY_WINDOW'),
    ('TARGET_EXHAUSTION_RISK_SCORE_BY_WINDOW'),
    ('TARGET_LIQUIDITY_TRADABILITY_SCORE'),
    ('TARGET_NOISE_SCORE_BY_WINDOW'),
    ('TARGET_PATH_STABILITY_SCORE_BY_WINDOW'),
    ('TARGET_STATE_PERSISTENCE_SCORE_BY_WINDOW'),
    ('TARGET_STATE_TRADABILITY_SCORE_BY_WINDOW'),
    ('TARGET_TRANSITION_RISK_SCORE_BY_WINDOW'),
    ('TARGET_TREND_QUALITY_SCORE_BY_WINDOW')
)
DELETE FROM trading_registry r
WHERE r.kind = 'state_vector_value'
  AND NOT EXISTS (
    SELECT 1 FROM core_scores WHERE core_scores.key = r.key
  );
