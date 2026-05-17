-- Register the current physical Layer 4 model-output surface name.

INSERT INTO trading_registry (
  id,
  kind,
  key,
  payload_format,
  payload,
  path,
  applies_to,
  artifact_sync_policy,
  note
) VALUES (
  'trm_MEFR001',
  'term',
  'MODEL_04_EVENT_FAILURE_RISK',
  'text',
  'model_04_event_failure_risk',
  'trading-model/docs/13_layer_04_event_failure_risk.md',
  'trading-model;event_failure_risk_model;event_failure_risk_vector;layer_04_event_failure_risk;current_physical_names',
  'registry_only',
  'Accepted current physical model_04_event_failure_risk model-output surface name for Layer 4 EventFailureRiskModel outputs. Layer 4 consumes only reviewed event/strategy-failure evidence packets and does not emit action, sizing, option-expression, execution, or broker/account mutation instructions.'
)
ON CONFLICT (id) DO UPDATE SET
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note,
  updated_at = NOW();
