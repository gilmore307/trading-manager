-- Keep Layer 3 handoff fields separate from direction-neutral score families.

UPDATE trading_registry
SET payload = REPLACE(payload, ';3_target_handoff_state;3_target_handoff_bias;3_target_handoff_rank;3_target_selection_reason_codes', ''),
    note = 'Reviewed TargetStateVector V1 direction-neutral score families. Direction scores are signed state evidence, not quality, final action, or position sizing. Target handoff fields are registered separately because they rank anonymous candidates inside a fixed candidate-policy batch rather than scoring state quality.',
    updated_at = NOW()
WHERE key = 'TARGET_STATE_VECTOR_DIRECTION_NEUTRAL_SCORE_FAMILIES';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_TSVH001',
    'config',
    'TARGET_STATE_VECTOR_HANDOFF_FIELDS',
    'text',
    '3_target_handoff_state;3_target_handoff_bias;3_target_handoff_rank;3_target_selection_reason_codes',
    'trading-model/src/models/model_03_target_state_vector/target_state_vector_contract.md',
    'target_context_state;model_03_target_state_vector;target_state_vector_model;candidate_policy_batch;target_handoff',
    'registry_only',
    'Reviewed TargetStateVector V1 handoff fields for anonymous candidate-policy batch ranking. These fields are target-selection evidence, not alpha confidence, portfolio weights, option expressions, orders, or execution policy.'
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
