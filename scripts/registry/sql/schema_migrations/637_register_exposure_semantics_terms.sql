-- Register and normalize shared exposure semantics for Layer 7/8 boundaries.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_NRE001',
    'term',
    'NORMALIZED_RISK_EXPOSURE',
    'text',
    'normalized_risk_exposure',
    'trading-model/docs/21_vector_taxonomy.md',
    'position_projection_model;underlying_action_model;dynamic_risk_policy_model;execution_risk_control',
    'registry_only',
    'Shared modeling term for signed abstract risk exposure normalized to the accepted strategy/risk budget scale. It is not shares, contracts, notional dollars, portfolio percentage, order quantity, or broker execution size.'
  ),
  (
    'trm_TEX001',
    'term',
    'TARGET_EXPOSURE',
    'text',
    'target_exposure',
    'trading-model/docs/16_layer_07_position_projection.md',
    'position_projection_model;position_projection_vector;underlying_action_model',
    'registry_only',
    'Layer 7 target holding-state exposure after alpha, risk budget, current/pending position, cost, liquidity, path risk, and stability compression. It is a normalized risk exposure target, not actual holdings, order quantity, or a planned action.'
  ),
  (
    'trm_CPE001',
    'term',
    'CURRENT_POSITION_EXPOSURE',
    'text',
    'current_position_exposure',
    'trading-model/docs/16_layer_07_position_projection.md',
    'position_projection_model;current_position_state;position_projection_vector',
    'registry_only',
    'Layer 7 point-in-time normalized exposure currently held before pending-order adjustment. It is position-state evidence, not broker quantity, not current account percentage, and not an instruction to maintain or change the position.'
  ),
  (
    'trm_PEX001',
    'term',
    'PENDING_EXPOSURE',
    'text',
    'pending_exposure',
    'trading-model/docs/16_layer_07_position_projection.md',
    'position_projection_model;pending_position_state;position_projection_vector',
    'registry_only',
    'Layer 7 normalized exposure represented by pending orders or pending adjustment state before fill-probability weighting. It is used to avoid duplicate projection pressure and is not a new order instruction.'
  ),
  (
    'trm_PGAP001',
    'term',
    'POSITION_GAP',
    'text',
    'position_gap',
    'trading-model/docs/16_layer_07_position_projection.md',
    'position_projection_model;position_projection_vector;underlying_action_model',
    'registry_only',
    'Layer 7 target exposure minus effective current exposure. It is adjustment-pressure evidence for Layer 8 planned-action review, not an execution instruction and not itself open/increase/reduce/close/maintain/no_trade.'
  )
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

UPDATE trading_registry
SET note = 'Layer 7 point-in-time current position state input. It describes current abstract normalized exposure, direction, age, liquidity, and risk/concentration context; it is not an order or execution record.',
    updated_at = now()
WHERE kind = 'term'
  AND key = 'CURRENT_POSITION_STATE';

UPDATE trading_registry
SET note = 'Layer 7 point-in-time pending position state input. Pending exposure is adjusted by fill probability to calculate effective current exposure and avoid repeated projection pressure.',
    updated_at = now()
WHERE kind = 'term'
  AND key = 'PENDING_POSITION_STATE';

UPDATE trading_registry
SET note = 'Layer 7 model-local exposure construct: current_position_exposure plus pending_exposure_size times pending_order_fill_probability_estimate. Used to compute position gap; not an execution instruction.',
    updated_at = now()
WHERE kind = 'term'
  AND key = 'EFFECTIVE_CURRENT_EXPOSURE';

UPDATE trading_registry
SET note = 'Accepted canonical Layer 7 model id. PositionProjectionModel maps final adjusted alpha confidence plus current/pending position, position-level friction, portfolio exposure, and risk-budget context to projected target holding state; current physical surface is model_07_position_projection.',
    updated_at = now()
WHERE kind = 'term'
  AND key = 'POSITION_PROJECTION_MODEL';

UPDATE trading_registry
SET note = 'Layer 7 signed normalized abstract target risk exposure by horizon. This is not shares, contracts, position size, order quantity, or final action.',
    updated_at = now()
WHERE kind = 'state_vector_value'
  AND key = 'POSITION_TARGET_EXPOSURE_SCORE_BY_HORIZON';

UPDATE trading_registry
SET note = 'Layer 7 signed score family for target exposure minus effective current exposure by horizon. This is a state gap, not an execution instruction.',
    updated_at = now()
WHERE kind = 'state_vector_value'
  AND key = 'POSITION_GAP_SCORE_BY_HORIZON';

UPDATE trading_registry
SET note = 'Layer 7 high-is-bad score family for relative cost pressure required to close the position gap by horizon. It is not a no-trade action.',
    updated_at = now()
WHERE kind = 'state_vector_value'
  AND key = 'COST_TO_ADJUST_POSITION_SCORE_BY_HORIZON';

UPDATE trading_registry
SET note = 'Layer 7 high-is-good score family for how closely current plus pending exposure already matches projected target exposure by horizon.',
    updated_at = now()
WHERE kind = 'state_vector_value'
  AND key = 'CURRENT_POSITION_ALIGNMENT_SCORE_BY_HORIZON';

UPDATE trading_registry
SET note = 'Layer 7 signed score family for expected risk-adjusted net utility of the projected target holding state after position-level friction and risk penalties.',
    updated_at = now()
WHERE kind = 'state_vector_value'
  AND key = 'EXPECTED_POSITION_UTILITY_SCORE_BY_HORIZON';

UPDATE trading_registry
SET note = 'Layer 7 high-is-large score family for absolute normalized distance between target exposure and effective current exposure by horizon.',
    updated_at = now()
WHERE kind = 'state_vector_value'
  AND key = 'POSITION_GAP_MAGNITUDE_SCORE_BY_HORIZON';

UPDATE trading_registry
SET note = 'Layer 7 high-is-good score family for confidence in mapping alpha confidence plus position/cost/risk state into target holding-state projection. This is separate from Layer 5 alpha confidence.',
    updated_at = now()
WHERE kind = 'state_vector_value'
  AND key = 'POSITION_PROJECTION_CONFIDENCE_SCORE_BY_HORIZON';

UPDATE trading_registry
SET note = 'Layer 7 high-is-good score family for stability of the projected target holding state across alpha, horizon, cost, risk-budget, and pending-order uncertainty.',
    updated_at = now()
WHERE kind = 'state_vector_value'
  AND key = 'POSITION_STATE_STABILITY_SCORE_BY_HORIZON';

UPDATE trading_registry
SET note = 'Layer 7 high-is-good score family for target exposure compatibility with current risk budget, drawdown, concentration, and portfolio exposure constraints.',
    updated_at = now()
WHERE kind = 'state_vector_value'
  AND key = 'RISK_BUDGET_FIT_SCORE_BY_HORIZON';

UPDATE trading_registry
SET note = 'Layer 7 signed target holding-direction bias by horizon. Positive is long exposure bias and negative is short exposure bias; this is not buy/sell/hold.',
    updated_at = now()
WHERE kind = 'state_vector_value'
  AND key = 'TARGET_POSITION_BIAS_SCORE_BY_HORIZON';

UPDATE trading_registry
SET note = 'Reviewed Layer 7 diagnostic field-family tokens for raw alpha-to-position priors, effective exposure calculations, and risk/cost reason-code attribution. Diagnostics are not default Layer 7-facing state_vector_value rows.',
    updated_at = now()
WHERE kind = 'config'
  AND key = 'POSITION_PROJECTION_DIAGNOSTIC_FIELD_FAMILIES';

UPDATE trading_registry
SET note = 'Reviewed position-projection handoff summary field-family tokens for communicating resolved target holding state from Layer 7 PositionProjectionModel to Layer 8 UnderlyingActionModel. Current physical 7_* / model_07 names are active. These are not buy/sell/hold, planned quantities, order instructions, or option-expression fields.',
    updated_at = now()
WHERE kind = 'config'
  AND key = 'POSITION_PROJECTION_HANDOFF_SUMMARY_FIELDS';

UPDATE trading_registry
SET payload = 'effective_current_underlying_exposure_score;pending_adjusted_underlying_exposure_score;underlying_exposure_gap_score;hard_gate_reason_codes;soft_gate_reason_codes;risk_plan_reason_codes;layer_9_handoff_reason_codes',
    note = 'Reviewed Layer 8 diagnostic field-family tokens for effective underlying exposure calculations, gate decisions, risk-plan attribution, and Layer 9 handoff attribution. Diagnostics are not default scalar score-family rows and do not authorize broker execution.',
    updated_at = now()
WHERE kind = 'config'
  AND key = 'UNDERLYING_ACTION_DIAGNOSTIC_FIELD_FAMILIES';
