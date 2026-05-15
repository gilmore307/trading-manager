-- Register abnormality coverage completion gate for activity-price proof.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_ABNCOV001',
    'config',
    'ABNORMALITY_COVERAGE_COMPLETE_REQUIRED_FAMILIES',
    'text',
    'price_action_pattern;residual_market_structure_disturbance;microstructure_liquidity_disruption;option_derivatives_abnormality',
    'trading-model/docs/99_activity_price_relationship_study.md',
    'activity_price_relationship_study;event_activity_bridge;abnormal_activity;proof_gate',
    'sync_artifact',
    'Accepted abnormal-activity families that must be represented before directional or promotion judgment.'
  ),
  (
    'cfg_ABNCOV002',
    'config',
    'OPTION_ABNORMALITY_COVERAGE_COMPLETE_REQUIRED_EVIDENCE',
    'text',
    'call_put_side;aggressor_or_quote_side;ask_bid_touch_context;sweep_or_block_context;opening_or_closing_context;open_interest_or_oi_change;iv_level_and_change;skew_direction;term_structure_direction;underlying_confirmation_or_divergence;direction_confidence',
    'trading-model/docs/99_activity_price_relationship_study.md',
    'option_activity;activity_direction;event_activity_bridge;proof_gate',
    'sync_artifact',
    'Required option abnormality evidence before final bullish/bearish direction judgment. Partial pilots remain diagnostic only.'
  ),
  (
    'cfg_ABNCOV003',
    'config',
    'ABNORMALITY_INCOMPLETE_DIAGNOSTIC_STATUS',
    'text',
    'diagnostic_only_abnormality_incomplete',
    'trading-model/docs/99_activity_price_relationship_study.md',
    'activity_price_relationship_study;model_promotion;manager_review',
    'sync_artifact',
    'Status for pilots that may debug label shape but cannot support final directional conclusion or model-layer promotion.'
  ),
  (
    'cfg_ABNCOV004',
    'config',
    'ABNORMALITY_COVERAGE_BEFORE_CROSS_SECTION_JUDGMENT_POLICY',
    'text',
    'complete_abnormality_evidence_before_final_judgment;adding_symbols_does_not_fix_missing_abnormality_fields;pilots_may_find_hypotheses_but_must_not_promote',
    'trading-manager/docs/81_decision.md',
    'activity_price_relationship_study;manager_control_plane;proof_gate',
    'sync_artifact',
    'Manager policy: cross-sectional breadth cannot substitute for missing abnormality evidence fields.'
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
