-- Register Layer 8 planned exposure-change semantics.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'trm_PEC001',
  'term',
  'PLANNED_EXPOSURE_CHANGE',
  'text',
  'planned_exposure_change',
  'trading-model/docs/17_layer_08_underlying_action.md',
  'underlying_action_model;underlying_action_plan;underlying_action_vector;execution_risk_control',
  'registry_only',
  'Layer 8 planned normalized exposure delta proposed by the offline underlying action plan after conservative action gating. It is not final order quantity, not shares/contracts/notional, not broker route, and not authorization to execute.'
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
