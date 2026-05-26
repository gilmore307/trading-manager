-- Register current Layer 3-10 model-layer tokens for scripts that resolve
-- model-layer values by stable registry id.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('mlv_L3TSV01', 'term', 'MODEL_LAYER_LAYER_03_TARGET_STATE_VECTOR', 'text', 'layer_03_target_state_vector', 'trading-manager/docs/28_numbering_physical_contract.md', 'model_layer;target_state_vector_model;realtime_shadow_handoff', 'registry_only', 'Reviewed model_layer value for Layer 3 TargetStateVectorModel.'),
  ('mlv_L4EFR001', 'term', 'MODEL_LAYER_LAYER_04_EVENT_FAILURE_RISK', 'text', 'layer_04_event_failure_risk', 'trading-manager/docs/28_numbering_physical_contract.md', 'model_layer;event_failure_risk_model;realtime_shadow_handoff', 'registry_only', 'Reviewed model_layer value for Layer 4 EventFailureRiskModel.'),
  ('mlv_L5AC001', 'term', 'MODEL_LAYER_LAYER_05_ALPHA_CONFIDENCE', 'text', 'layer_05_alpha_confidence', 'trading-manager/docs/28_numbering_physical_contract.md', 'model_layer;alpha_confidence_model;realtime_shadow_handoff', 'registry_only', 'Reviewed model_layer value for Layer 5 AlphaConfidenceModel.'),
  ('mlv_L6DRP001', 'term', 'MODEL_LAYER_LAYER_06_DYNAMIC_RISK_POLICY', 'text', 'layer_06_dynamic_risk_policy', 'trading-manager/docs/28_numbering_physical_contract.md', 'model_layer;dynamic_risk_policy_model;realtime_shadow_handoff', 'registry_only', 'Reviewed model_layer value for Layer 6 DynamicRiskPolicyModel.'),
  ('mlv_L7PP001', 'term', 'MODEL_LAYER_LAYER_07_POSITION_PROJECTION', 'text', 'layer_07_position_projection', 'trading-manager/docs/28_numbering_physical_contract.md', 'model_layer;position_projection_model;realtime_shadow_handoff', 'registry_only', 'Reviewed model_layer value for Layer 7 PositionProjectionModel.'),
  ('mlv_L8UA001', 'term', 'MODEL_LAYER_LAYER_08_UNDERLYING_ACTION', 'text', 'layer_08_underlying_action', 'trading-manager/docs/28_numbering_physical_contract.md', 'model_layer;underlying_action_model;realtime_shadow_handoff', 'registry_only', 'Reviewed model_layer value for Layer 8 UnderlyingActionModel.'),
  ('mlv_L9OE001', 'term', 'MODEL_LAYER_LAYER_09_OPTION_EXPRESSION', 'text', 'layer_09_option_expression', 'trading-manager/docs/28_numbering_physical_contract.md', 'model_layer;option_expression_model;realtime_shadow_handoff', 'registry_only', 'Reviewed model_layer value for Layer 9 OptionExpressionModel.'),
  ('mlv_L10ERG001', 'term', 'MODEL_LAYER_LAYER_10_EVENT_RISK_GOVERNOR', 'text', 'layer_10_event_risk_governor', 'trading-manager/docs/28_numbering_physical_contract.md', 'model_layer;event_risk_governor;realtime_shadow_handoff', 'registry_only', 'Reviewed model_layer value for Layer 10 EventRiskGovernor.')
ON CONFLICT (id) DO UPDATE SET
    kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();
