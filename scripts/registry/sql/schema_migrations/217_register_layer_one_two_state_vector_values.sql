-- Register Layer 1 and Layer 2 model state-vector values explicitly.
-- Physical model-output columns remain registered as field rows; these rows add the
-- semantic model-state/vector token layer so registry consumers can query all
-- accepted model state-vector values through kind=state_vector_value.

WITH layer_one_values(id, key, source_key, note) AS (
  VALUES
    ('svv_MRMV22001', 'MODEL_01_MARKET_DIRECTION_SCORE_VALUE', 'MARKET_DIRECTION_SCORE', 'Layer 1 MarketRegime state-vector value for signed broad market direction evidence; sign is not a trade instruction or quality score.'),
    ('svv_MRMV22002', 'MODEL_01_MARKET_DIRECTION_STRENGTH_SCORE_VALUE', 'MARKET_DIRECTION_STRENGTH_SCORE', 'Layer 1 MarketRegime state-vector value for broad market direction-evidence magnitude, separated from signed direction and trend quality.'),
    ('svv_MRMV22003', 'MODEL_01_MARKET_TREND_QUALITY_SCORE_VALUE', 'MARKET_TREND_QUALITY_SCORE', 'Layer 1 MarketRegime state-vector value for direction-neutral broad market trend clarity and structural quality.'),
    ('svv_MRMV22004', 'MODEL_01_MARKET_STABILITY_SCORE_VALUE', 'MARKET_STABILITY_SCORE', 'Layer 1 MarketRegime state-vector value for broad market stability and resistance to whipsaw/noise.'),
    ('svv_MRMV22005', 'MODEL_01_MARKET_RISK_STRESS_SCORE_VALUE', 'MARKET_RISK_STRESS_SCORE', 'Layer 1 MarketRegime state-vector value for broad risk/stress pressure; higher values indicate worse stress.'),
    ('svv_MRMV22006', 'MODEL_01_MARKET_TRANSITION_RISK_SCORE_VALUE', 'MARKET_TRANSITION_RISK_SCORE', 'Layer 1 MarketRegime state-vector value for transition/decay/fragility risk in the broad market state.'),
    ('svv_MRMV22007', 'MODEL_01_BREADTH_PARTICIPATION_SCORE_VALUE', 'BREADTH_PARTICIPATION_SCORE', 'Layer 1 MarketRegime state-vector value for broad participation and breadth support.'),
    ('svv_MRMV22008', 'MODEL_01_CORRELATION_CROWDING_SCORE_VALUE', 'CORRELATION_CROWDING_SCORE', 'Layer 1 MarketRegime state-vector value for correlation/crowding and risk-on/risk-off background.'),
    ('svv_MRMV22009', 'MODEL_01_DISPERSION_OPPORTUNITY_SCORE_VALUE', 'DISPERSION_OPPORTUNITY_SCORE', 'Layer 1 MarketRegime state-vector value for broad dispersion/opportunity context.'),
    ('svv_MRMV22010', 'MODEL_01_MARKET_LIQUIDITY_PRESSURE_SCORE_VALUE', 'MARKET_LIQUIDITY_PRESSURE_SCORE', 'Layer 1 MarketRegime state-vector value for market-wide liquidity pressure or cost stress.'),
    ('svv_MRMV22011', 'MODEL_01_MARKET_LIQUIDITY_SUPPORT_SCORE_VALUE', 'MARKET_LIQUIDITY_SUPPORT_SCORE', 'Layer 1 MarketRegime state-vector value for market-wide liquidity support and practical tradability.'),
    ('svv_MRMV22012', 'MODEL_01_MARKET_COVERAGE_SCORE_VALUE', 'MARKET_COVERAGE_SCORE', 'Layer 1 MarketRegime state-vector value for source/feature coverage supporting the market state row.'),
    ('svv_MRMV22013', 'MODEL_01_MARKET_DATA_QUALITY_SCORE_VALUE', 'MARKET_DATA_QUALITY_SCORE', 'Layer 1 MarketRegime state-vector value for data quality supporting the market state row.')
), layer_two_values(id, key, source_key, note) AS (
  VALUES
    ('svv_SCMV22001', 'MODEL_02_SECTOR_RELATIVE_DIRECTION_SCORE_VALUE', 'SECTOR_RELATIVE_DIRECTION_SCORE', 'Layer 2 SectorContext state-vector value for signed current sector-vs-market direction evidence; sign is not quality, weight, or action.'),
    ('svv_SCMV22002', 'MODEL_02_SECTOR_TREND_QUALITY_SCORE_VALUE', 'SECTOR_TREND_QUALITY_SCORE', 'Layer 2 SectorContext state-vector value for direction-neutral sector trend clarity and structural quality.'),
    ('svv_SCMV22003', 'MODEL_02_SECTOR_TREND_STABILITY_SCORE_VALUE', 'SECTOR_TREND_STABILITY_SCORE', 'Layer 2 SectorContext state-vector value for sector trend persistence/smoothness and resistance to whipsaw.'),
    ('svv_SCMV22004', 'MODEL_02_SECTOR_TRANSITION_RISK_SCORE_VALUE', 'SECTOR_TRANSITION_RISK_SCORE', 'Layer 2 SectorContext state-vector value for sector transition/decay/fragility risk; higher values indicate more risk.'),
    ('svv_SCMV22005', 'MODEL_02_MARKET_CONTEXT_SUPPORT_SCORE_VALUE', 'MARKET_CONTEXT_SUPPORT_SCORE', 'Layer 2 SectorContext state-vector value for market-context support quality inherited from Layer 1 conditioning.'),
    ('svv_SCMV22006', 'MODEL_02_SECTOR_BREADTH_CONFIRMATION_SCORE_VALUE', 'SECTOR_BREADTH_CONFIRMATION_SCORE', 'Layer 2 SectorContext state-vector value for internal/peer confirmation that sector movement is broad rather than isolated.'),
    ('svv_SCMV22007', 'MODEL_02_SECTOR_DISPERSION_CROWDING_SCORE_VALUE', 'SECTOR_DISPERSION_CROWDING_SCORE', 'Layer 2 SectorContext state-vector value for dispersion/crowding pressure that can make the sector harder to trade.'),
    ('svv_SCMV22008', 'MODEL_02_SECTOR_LIQUIDITY_TRADABILITY_SCORE_VALUE', 'SECTOR_LIQUIDITY_TRADABILITY_SCORE', 'Layer 2 SectorContext state-vector value for basket/candidate-pool liquidity, spread, and capacity support.'),
    ('svv_SCMV22009', 'MODEL_02_SECTOR_TRADABILITY_SCORE_VALUE', 'SECTOR_TRADABILITY_SCORE', 'Layer 2 SectorContext state-vector value for direction-neutral sector tradability and handoff quality.'),
    ('svv_SCMV22010', 'MODEL_02_SECTOR_HANDOFF_STATE_VALUE', 'SECTOR_HANDOFF_STATE', 'Layer 2 SectorContext state-vector value for downstream handoff state; selected/watch/blocked/insufficient_data is not an action instruction.'),
    ('svv_SCMV22011', 'MODEL_02_SECTOR_HANDOFF_BIAS_VALUE', 'SECTOR_HANDOFF_BIAS', 'Layer 2 SectorContext state-vector value for separate handoff bias; long/short sign is not quality or size.'),
    ('svv_SCMV22012', 'MODEL_02_SECTOR_HANDOFF_RANK_VALUE', 'SECTOR_HANDOFF_RANK', 'Layer 2 SectorContext state-vector value for optional selected/watch basket priority rank; not a portfolio weight.'),
    ('svv_SCMV22013', 'MODEL_02_SECTOR_HANDOFF_REASON_CODES_VALUE', 'SECTOR_HANDOFF_REASON_CODES', 'Layer 2 SectorContext state-vector value for stable reason codes explaining handoff state and bias decisions.'),
    ('svv_SCMV22014', 'MODEL_02_SECTOR_ELIGIBILITY_STATE_VALUE', 'SECTOR_ELIGIBILITY_STATE', 'Layer 2 SectorContext state-vector value for row eligibility: eligible/watch/excluded/insufficient_data.'),
    ('svv_SCMV22015', 'MODEL_02_SECTOR_ELIGIBILITY_REASON_CODES_VALUE', 'SECTOR_ELIGIBILITY_REASON_CODES', 'Layer 2 SectorContext state-vector value for stable reason codes explaining eligibility/watch/excluded/insufficient rows.'),
    ('svv_SCMV22016', 'MODEL_02_SECTOR_STATE_QUALITY_SCORE_VALUE', 'SECTOR_STATE_QUALITY_SCORE', 'Layer 2 SectorContext state-vector value for reliability/completeness of the produced sector state row.'),
    ('svv_SCMV22017', 'MODEL_02_SECTOR_COVERAGE_SCORE_VALUE', 'SECTOR_COVERAGE_SCORE', 'Layer 2 SectorContext state-vector value for coverage supporting the sector state row.'),
    ('svv_SCMV22018', 'MODEL_02_SECTOR_DATA_QUALITY_SCORE_VALUE', 'SECTOR_DATA_QUALITY_SCORE', 'Layer 2 SectorContext state-vector value for data quality supporting the sector state row.'),
    ('svv_SCMV22019', 'MODEL_02_SECTOR_EVIDENCE_COUNT_VALUE', 'SECTOR_EVIDENCE_COUNT', 'Layer 2 SectorContext state-vector value for count of usable evidence fields contributing to the sector state row.')
), new_values AS (
  SELECT * FROM layer_one_values
  UNION ALL
  SELECT * FROM layer_two_values
)
INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
SELECT
  new_values.id,
  'state_vector_value',
  new_values.key,
  source.payload_format,
  source.payload,
  COALESCE(NULLIF(source.path, ''), CASE WHEN source.applies_to LIKE '%model_01_market_regime%' THEN 'trading-model/docs/02_layer_01_market_regime.md' ELSE source.path END),
  source.applies_to,
  'registry_only',
  new_values.note
FROM new_values
JOIN trading_registry source ON source.key = new_values.source_key
ON CONFLICT (id) DO UPDATE SET
    kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = CURRENT_TIMESTAMP;

-- Existing Layer 2 enum rows are not generic glossary terms; they are fixed
-- values inside the SectorContext state-vector contract.
UPDATE trading_registry
SET kind = 'state_vector_value',
    applies_to = CASE
      WHEN applies_to LIKE '%sector_context_state%' THEN applies_to
      ELSE applies_to || ';sector_context_state;sector_context_model'
    END,
    updated_at = CURRENT_TIMESTAMP
WHERE id IN (
  'trm_SCMHS001', 'trm_SCMHS002', 'trm_SCMHS003', 'trm_SCMHS004',
  'trm_SCMB001', 'trm_SCMB002', 'trm_SCMB003', 'trm_SCMB004'
);

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('svv_SCME001', 'state_vector_value', 'SECTOR_ELIGIBILITY_STATE_ELIGIBLE', 'text', 'eligible', 'trading-model/src/models/model_02_sector_context/sector_context_state_contract.md', '2_eligibility_state;model_02_sector_context;sector_context_state;sector_context_model', 'registry_only', 'Layer 2 eligibility-state value: sector/industry basket has enough point-in-time evidence and passes eligibility gates.'),
  ('svv_SCME002', 'state_vector_value', 'SECTOR_ELIGIBILITY_STATE_WATCH', 'text', 'watch', 'trading-model/src/models/model_02_sector_context/sector_context_state_contract.md', '2_eligibility_state;model_02_sector_context;sector_context_state;sector_context_model', 'registry_only', 'Layer 2 eligibility-state value: sector/industry basket is retained for observation but needs caution or more evidence.'),
  ('svv_SCME003', 'state_vector_value', 'SECTOR_ELIGIBILITY_STATE_EXCLUDED', 'text', 'excluded', 'trading-model/src/models/model_02_sector_context/sector_context_state_contract.md', '2_eligibility_state;model_02_sector_context;sector_context_state;sector_context_model', 'registry_only', 'Layer 2 eligibility-state value: sector/industry basket is excluded from downstream handoff.'),
  ('svv_SCME004', 'state_vector_value', 'SECTOR_ELIGIBILITY_STATE_INSUFFICIENT_DATA', 'text', 'insufficient_data', 'trading-model/src/models/model_02_sector_context/sector_context_state_contract.md', '2_eligibility_state;model_02_sector_context;sector_context_state;sector_context_model', 'registry_only', 'Layer 2 eligibility-state value: point-in-time evidence is insufficient for sector context use.')
ON CONFLICT (id) DO UPDATE SET
    kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = CURRENT_TIMESTAMP;
