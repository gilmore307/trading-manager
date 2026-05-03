-- Register the Layer 2 model explainability and diagnostics artifact names.
-- The primary downstream contract remains trading_model.model_02_sector_context;
-- support artifacts own review/debug/acceptance evidence and are not hard
-- downstream prediction dependencies.
UPDATE trading_registry
SET
  path = 'trading-model/docs/03_layer_02_sector_context.md',
  applies_to = 'trading-model;sector_context_model;feature_02_sector_context',
  note = 'Accepted Layer 2 SectorContextModel model-output term for sector_context_state; primary physical output table is trading_model.model_02_sector_context. Support artifacts hold explainability and diagnostics evidence and should not become hard downstream prediction dependencies without a later reviewed promotion decision.',
  updated_at = CURRENT_TIMESTAMP
WHERE id = 'trm_M2S001';

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
) VALUES
  (
    'trm_SCMEXPL',
    'term',
    'MODEL_02_SECTOR_CONTEXT_EXPLAINABILITY',
    'text',
    'model_02_sector_context_explainability',
    'trading-model/docs/03_layer_02_sector_context.md',
    'trading-model;sector_context_model;model_02_sector_context',
    'registry_only',
    'Accepted Layer 2 SectorContextModel explainability artifact/table name. Owns human-review behavior internals, inferred attributes, conditional behavior, contributing evidence, and reason-code detail; downstream production logic should not hard-depend on this artifact.'
  ),
  (
    'trm_SCMDIAG',
    'term',
    'MODEL_02_SECTOR_CONTEXT_DIAGNOSTICS',
    'text',
    'model_02_sector_context_diagnostics',
    'trading-model/docs/03_layer_02_sector_context.md',
    'trading-model;sector_context_model;model_02_sector_context',
    'registry_only',
    'Accepted Layer 2 SectorContextModel diagnostics artifact/table name. Owns acceptance, monitoring, and gating evidence such as tradability, event/gap/volatility/correlation stress, freshness, missingness, baseline comparison, refit stability, and no-future-leak checks.'
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
