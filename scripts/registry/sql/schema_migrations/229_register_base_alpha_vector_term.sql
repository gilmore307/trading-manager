-- Register the Layer 5 base/unadjusted alpha diagnostic vector term.
-- The vector is a reviewed model-local diagnostic surface used for attribution and
-- debugging. It is not the default Layer 6-facing alpha_confidence_vector output.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'trm_BAV001',
  'term',
  'BASE_ALPHA_VECTOR',
  'text',
  'base_alpha_vector',
  'trading-model/docs/06_layer_05_alpha_confidence.md',
  'trading-model;alpha_confidence_model;model_05_alpha_confidence;market_context_state;sector_context_state;target_context_state;diagnostics;event_adjustment_attribution',
  'registry_only',
  'Layer 5 base/unadjusted alpha diagnostic vector built from Layer 1/2/3 state evidence before EventOverlayModel correction. Used for research, audit, debugging, and event-adjustment attribution; not the default Layer 6-facing alpha_confidence_vector output.'
)
ON CONFLICT (id) DO UPDATE SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note;
