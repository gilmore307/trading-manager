-- Collapse Layer 1 and Layer 2 state-vector payload tokens out of field rows.
-- These reviewed model-contract payloads are state_vector_value rows, not dual
-- field/state_vector_value registrations. Physical storage-only columns can still
-- use field, but these payload tokens are owned by the state-vector contract.

WITH layer_one_field_rows(id, note) AS (
  VALUES
    ('fld_MRMV22001', 'Layer 1 MarketRegime state-vector value for signed broad market direction evidence; sign is not a trade instruction or quality score.'),
    ('fld_MRMV22002', 'Layer 1 MarketRegime state-vector value for broad market direction-evidence magnitude, separated from signed direction and trend quality.'),
    ('fld_MRMV22003', 'Layer 1 MarketRegime state-vector value for direction-neutral broad market trend clarity and structural quality.'),
    ('fld_MRMV22004', 'Layer 1 MarketRegime state-vector value for broad market stability and resistance to whipsaw/noise.'),
    ('fld_MRMV22005', 'Layer 1 MarketRegime state-vector value for broad risk/stress pressure; higher values indicate worse stress.'),
    ('fld_MRMV22006', 'Layer 1 MarketRegime state-vector value for transition/decay/fragility risk in the broad market state.'),
    ('fld_MRMV22007', 'Layer 1 MarketRegime state-vector value for broad participation and breadth support.'),
    ('fld_MRMV22008', 'Layer 1 MarketRegime state-vector value for correlation/crowding and risk-on/risk-off background.'),
    ('fld_MRMV22009', 'Layer 1 MarketRegime state-vector value for broad dispersion/opportunity context.'),
    ('fld_MRMV22010', 'Layer 1 MarketRegime state-vector value for market-wide liquidity pressure or cost stress.'),
    ('fld_MRMV22011', 'Layer 1 MarketRegime state-vector value for market-wide liquidity support and practical tradability.'),
    ('fld_MRMV22012', 'Layer 1 MarketRegime state-vector value for source/feature coverage supporting the market state row.'),
    ('fld_MRMV22013', 'Layer 1 MarketRegime state-vector value for data quality supporting the market state row.')
), layer_two_field_rows(id, note) AS (
  VALUES
    ('fld_SCMV22001', 'Layer 2 SectorContext state-vector value for signed current sector-vs-market direction evidence; sign is not quality, weight, or action.'),
    ('fld_SCMV22002', 'Layer 2 SectorContext state-vector value for direction-neutral sector trend clarity and structural quality.'),
    ('fld_SCMV22003', 'Layer 2 SectorContext state-vector value for sector trend persistence/smoothness and resistance to whipsaw.'),
    ('fld_SCMV22004', 'Layer 2 SectorContext state-vector value for sector transition/decay/fragility risk; higher values indicate more risk.'),
    ('fld_SCMV22005', 'Layer 2 SectorContext state-vector value for market-context support quality inherited from Layer 1 conditioning.'),
    ('fld_SCMV22006', 'Layer 2 SectorContext state-vector value for internal/peer confirmation that sector movement is broad rather than isolated.'),
    ('fld_SCMV22007', 'Layer 2 SectorContext state-vector value for dispersion/crowding pressure that can make the sector harder to trade.'),
    ('fld_SCMV22008', 'Layer 2 SectorContext state-vector value for basket/candidate-pool liquidity, spread, and capacity support.'),
    ('fld_SCMV22009', 'Layer 2 SectorContext state-vector value for direction-neutral sector tradability and handoff quality.'),
    ('fld_SCMV22010', 'Layer 2 SectorContext state-vector value for downstream handoff state; selected/watch/blocked/insufficient_data is not an action instruction.'),
    ('fld_SCMV22011', 'Layer 2 SectorContext state-vector value for separate handoff bias; long/short sign is not quality or size.'),
    ('fld_SCMV22012', 'Layer 2 SectorContext state-vector value for optional selected/watch basket priority rank; not a portfolio weight.'),
    ('fld_SCMV22013', 'Layer 2 SectorContext state-vector value for stable reason codes explaining handoff state and bias decisions.'),
    ('fld_SCMV22014', 'Layer 2 SectorContext state-vector value for row eligibility: eligible/watch/excluded/insufficient_data.'),
    ('fld_SCMV22015', 'Layer 2 SectorContext state-vector value for stable reason codes explaining eligibility/watch/excluded/insufficient rows.'),
    ('fld_SCMV22016', 'Layer 2 SectorContext state-vector value for reliability/completeness of the produced sector state row.'),
    ('fld_SCMV22017', 'Layer 2 SectorContext state-vector value for coverage supporting the sector state row.'),
    ('fld_SCMV22018', 'Layer 2 SectorContext state-vector value for data quality supporting the sector state row.'),
    ('fld_SCMV22019', 'Layer 2 SectorContext state-vector value for count of usable evidence fields contributing to the sector state row.')
), target_rows AS (
  SELECT * FROM layer_one_field_rows
  UNION ALL
  SELECT * FROM layer_two_field_rows
)
UPDATE trading_registry r
SET kind = 'state_vector_value',
    artifact_sync_policy = 'registry_only',
    note = target_rows.note,
    updated_at = CURRENT_TIMESTAMP
FROM target_rows
WHERE r.id = target_rows.id;

-- Remove duplicate state_vector_value aliases created by the prior dual-registration
-- pass. The original reviewed keys stay on the existing fld_* ids, now classified
-- as state_vector_value.
DELETE FROM trading_registry
WHERE id LIKE 'svv_MRMV220%'
   OR id LIKE 'svv_SCMV220%';
