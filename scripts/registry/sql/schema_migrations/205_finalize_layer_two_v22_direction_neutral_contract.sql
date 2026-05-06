-- Finalize Layer 2 V2.2 direction-neutral SectorContextModel shared contract.
-- Layer 2 now separates signed sector direction, direction-neutral trend/tradability,
-- transition risk, state/data quality, handoff state, and handoff bias.

UPDATE trading_registry
SET note = 'Accepted Layer 2 SectorContextModel model-output term for direction-neutral sector_context_state. Primary physical output table is trading_model.model_02_sector_context and contains signed sector direction evidence, direction-neutral trend/tradability, transition risk, separate handoff state/bias, and row quality fields. It does not select final stocks, strategies, option contracts, position sizes, or final actions.',
    path = 'trading-model/docs/03_layer_02_sector_context.md',
    applies_to = 'trading-model;trading-data;trading-manager;trading-storage;sector_context_model;feature_02_sector_context;anonymous_target_candidate_builder',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'MODEL_02_SECTOR_CONTEXT';

UPDATE trading_registry
SET note = 'Conceptual Layer 2 SectorContextModel state: market-context-conditioned sector/industry basket state with signed relative direction kept separate from direction-neutral tradability, trend quality, transition risk, handoff bias, and reliability evidence.',
    path = 'trading-model/src/models/model_02_sector_context/sector_context_state_contract.md',
    applies_to = 'model_02_sector_context;sector_context_model;feature_02_sector_context;anonymous_target_candidate_builder',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'SECTOR_CONTEXT_STATE';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('fld_SCMV22001','field','SECTOR_RELATIVE_DIRECTION_SCORE','field_name','2_sector_relative_direction_score','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','model_02_sector_context;sector_context_state;sector_context_model','registry_only','Layer 2 signed current sector-vs-market direction evidence. Positive indicates relative long bias and negative indicates relative short bias; sign is not quality, weight, or action.'),
  ('fld_SCMV22002','field','SECTOR_TREND_QUALITY_SCORE','field_name','2_sector_trend_quality_score','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','model_02_sector_context;sector_context_state;sector_context_model','registry_only','Layer 2 direction-neutral clarity and structural quality of sector/industry trend behavior.'),
  ('fld_SCMV22003','field','SECTOR_TREND_STABILITY_SCORE','field_name','2_sector_trend_stability_score','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','model_02_sector_context;sector_context_state;sector_context_model','registry_only','Layer 2 direction-neutral persistence/smoothness of sector trend behavior and resistance to whipsaw.'),
  ('fld_SCMV22004','field','SECTOR_TRANSITION_RISK_SCORE','field_name','2_sector_transition_risk_score','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','model_02_sector_context;sector_context_state;sector_context_model','registry_only','Layer 2 risk that the sector state is switching, decaying, or becoming invalid. Higher means more transition risk.'),
  ('fld_SCMV22005','field','MARKET_CONTEXT_SUPPORT_SCORE','field_name','2_market_context_support_score','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','model_02_sector_context;sector_context_state;sector_context_model;model_01_market_regime','registry_only','Layer 2 current market-context support/headwind evidence for the sector state; this is not a copy of Layer 1 output fields.'),
  ('fld_SCMV22006','field','SECTOR_BREADTH_CONFIRMATION_SCORE','field_name','2_sector_breadth_confirmation_score','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','model_02_sector_context;sector_context_state;sector_context_model;feature_02_sector_context','registry_only','Layer 2 internal/peer breadth confirmation that sector movement is not isolated to a few large weights.'),
  ('fld_SCMV22007','field','SECTOR_DISPERSION_CROWDING_SCORE','field_name','2_sector_dispersion_crowding_score','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','model_02_sector_context;sector_context_state;sector_context_model;feature_02_sector_context','registry_only','Layer 2 dispersion/crowding pressure that can make the sector harder to trade. Higher means more pressure/risk.'),
  ('fld_SCMV22008','field','SECTOR_LIQUIDITY_TRADABILITY_SCORE','field_name','2_sector_liquidity_tradability_score','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','model_02_sector_context;sector_context_state;sector_context_model','registry_only','Layer 2 basket/candidate-pool liquidity, spread, and capacity support for downstream use.'),
  ('fld_SCMV22009','field','SECTOR_TRADABILITY_SCORE','field_name','2_sector_tradability_score','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','model_02_sector_context;sector_context_state;sector_context_model;anonymous_target_candidate_builder','registry_only','Layer 2 direction-neutral combined tradability score. High means clean sector context for downstream candidate construction whether long-biased or short-biased.'),
  ('fld_SCMV22010','field','SECTOR_HANDOFF_STATE','field_name','2_sector_handoff_state','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','model_02_sector_context;sector_context_state;sector_context_model;anonymous_target_candidate_builder','registry_only','Layer 2 downstream handoff state for anonymous target candidate construction: selected, watch, blocked, or insufficient_data.'),
  ('fld_SCMV22011','field','SECTOR_HANDOFF_BIAS','field_name','2_sector_handoff_bias','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','model_02_sector_context;sector_context_state;sector_context_model;anonymous_target_candidate_builder','registry_only','Layer 2 separate handoff bias value: long_bias, short_bias, neutral, or mixed. This must not be collapsed into handoff state or rank.'),
  ('fld_SCMV22012','field','SECTOR_HANDOFF_RANK','field_name','2_sector_handoff_rank','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','model_02_sector_context;sector_context_state;sector_context_model;anonymous_target_candidate_builder','registry_only','Optional Layer 2 priority rank among selected/watch sector baskets for downstream candidate construction; not a portfolio weight.'),
  ('fld_SCMV22013','field','SECTOR_HANDOFF_REASON_CODES','field_name','2_sector_handoff_reason_codes','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','model_02_sector_context;sector_context_state;sector_context_model;anonymous_target_candidate_builder','registry_only','Semicolon-separated Layer 2 reason codes explaining selected, watch, blocked, and bias decisions.'),
  ('fld_SCMV22014','field','SECTOR_ELIGIBILITY_STATE','field_name','2_eligibility_state','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','model_02_sector_context;sector_context_state;sector_context_model','registry_only','Layer 2 row eligibility state: eligible, watch, excluded, or insufficient_data.'),
  ('fld_SCMV22015','field','SECTOR_ELIGIBILITY_REASON_CODES','field_name','2_eligibility_reason_codes','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','model_02_sector_context;sector_context_state;sector_context_model','registry_only','Semicolon-separated Layer 2 reason codes explaining eligibility/watch/excluded/insufficient rows.'),
  ('fld_SCMV22016','field','SECTOR_STATE_QUALITY_SCORE','field_name','2_state_quality_score','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','model_02_sector_context;sector_context_state;sector_context_model','registry_only','Layer 2 reliability of the produced sector-context state row; not a tradability/opportunity score.'),
  ('fld_SCMV22017','field','SECTOR_COVERAGE_SCORE','field_name','2_coverage_score','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','model_02_sector_context;sector_context_state;sector_context_model;feature_02_sector_context','registry_only','Layer 2 evidence completeness/coverage summary; not trend certainty or opportunity.'),
  ('fld_SCMV22018','field','SECTOR_DATA_QUALITY_SCORE','field_name','2_data_quality_score','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','model_02_sector_context;sector_context_state;sector_context_model;feature_02_sector_context','registry_only','Layer 2 input freshness/reliability summary that may gate handoff.'),
  ('fld_SCMV22019','field','SECTOR_EVIDENCE_COUNT','field_name','2_evidence_count','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','model_02_sector_context;sector_context_state;sector_context_model;feature_02_sector_context','registry_only','Count of usable Layer 2 feature evidence fields/families contributing to the state row.')
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

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('trm_SCMHS001','term','SECTOR_HANDOFF_STATE_SELECTED','text','selected','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','2_sector_handoff_state;model_02_sector_context;anonymous_target_candidate_builder','registry_only','Layer 2 handoff state value: basket is accepted for downstream anonymous target candidate construction.'),
  ('trm_SCMHS002','term','SECTOR_HANDOFF_STATE_WATCH','text','watch','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','2_sector_handoff_state;model_02_sector_context;anonymous_target_candidate_builder','registry_only','Layer 2 handoff state value: basket is monitored but not strongly selected.'),
  ('trm_SCMHS003','term','SECTOR_HANDOFF_STATE_BLOCKED','text','blocked','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','2_sector_handoff_state;model_02_sector_context;anonymous_target_candidate_builder','registry_only','Layer 2 handoff state value: basket is blocked from downstream candidate construction.'),
  ('trm_SCMHS004','term','SECTOR_HANDOFF_STATE_INSUFFICIENT_DATA','text','insufficient_data','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','2_sector_handoff_state;model_02_sector_context;anonymous_target_candidate_builder','registry_only','Layer 2 handoff state value: point-in-time evidence is insufficient.'),
  ('trm_SCMB001','term','SECTOR_HANDOFF_BIAS_LONG_BIAS','text','long_bias','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','2_sector_handoff_bias;model_02_sector_context;anonymous_target_candidate_builder','registry_only','Layer 2 handoff bias value for relative long-bias sector context.'),
  ('trm_SCMB002','term','SECTOR_HANDOFF_BIAS_SHORT_BIAS','text','short_bias','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','2_sector_handoff_bias;model_02_sector_context;anonymous_target_candidate_builder','registry_only','Layer 2 handoff bias value for relative short-bias sector context.'),
  ('trm_SCMB003','term','SECTOR_HANDOFF_BIAS_NEUTRAL','text','neutral','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','2_sector_handoff_bias;model_02_sector_context;anonymous_target_candidate_builder','registry_only','Layer 2 handoff bias value for neutral sector context.'),
  ('trm_SCMB004','term','SECTOR_HANDOFF_BIAS_MIXED','text','mixed','trading-model/src/models/model_02_sector_context/sector_context_state_contract.md','2_sector_handoff_bias;model_02_sector_context;anonymous_target_candidate_builder','registry_only','Layer 2 handoff bias value for mixed or unresolved sector direction evidence.'),
  ('cfg_SCMP001','config','SECTOR_CONTEXT_PROMOTION_DIRECTION_NEUTRAL_THRESHOLDS','text','minimum_selected_bias_alignment_rate;minimum_selected_average_abs_label;minimum_selected_abs_label_lift_vs_blocked','trading-model/src/models/model_02_sector_context/config/promotion_thresholds.toml','model_02_sector_context;sector_context_model;model_evaluation;model_promotion','registry_only','Layer 2 V2.2 direction-neutral promotion thresholds. Handoff evaluation checks selected long/short bias alignment and absolute forward-path relationship instead of long-only selected_positive_rate.')
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
