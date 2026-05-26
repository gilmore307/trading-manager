-- Register model tokens that manager scripts need to resolve by stable id.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_MRM001',
    'term',
    'MARKET_REGIME_MODEL',
    'text',
    'market_regime_model',
    'trading-model/docs/10_layer_01_market_regime.md;trading-manager/docs/28_numbering_physical_contract.md',
    'trading-model;trading-manager;model_promotion;realtime_shadow_handoff;layer_01_market_regime',
    'registry_only',
    'Stable model id for MarketRegimeModel. Scripts should resolve this row by id instead of hard-coding the payload.'
  ),
  (
    'trm_DRPM001',
    'term',
    'DYNAMIC_RISK_POLICY_MODEL',
    'text',
    'dynamic_risk_policy_model',
    'trading-model/docs/02_architecture.md;trading-manager/docs/28_numbering_physical_contract.md',
    'trading-model;trading-manager;model_promotion;realtime_shadow_handoff;layer_06_dynamic_risk_policy',
    'registry_only',
    'Stable model id for DynamicRiskPolicyModel. Scripts should resolve this row by id instead of hard-coding the payload.'
  ),
  (
    'trm_M6DRP01',
    'term',
    'MODEL_06_DYNAMIC_RISK_POLICY',
    'text',
    'model_06_dynamic_risk_policy',
    'trading-model/docs/02_architecture.md;trading-manager/docs/28_numbering_physical_contract.md',
    'trading-model;trading-manager;model_sequence;realtime_shadow_handoff;layer_06_dynamic_risk_policy',
    'registry_only',
    'Stable physical package/table token for DynamicRiskPolicyModel in the current ten-layer sequence.'
  ),
  (
    'trm_DRPS001',
    'term',
    'DYNAMIC_RISK_POLICY_STATE',
    'text',
    'dynamic_risk_policy_state',
    'trading-model/docs/02_architecture.md;trading-manager/docs/28_numbering_physical_contract.md',
    'trading-model;trading-manager;model_output;realtime_shadow_handoff;layer_06_dynamic_risk_policy',
    'registry_only',
    'Stable output/state token for DynamicRiskPolicyModel runtime and rehearsal handoffs.'
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
    updated_at = NOW();
