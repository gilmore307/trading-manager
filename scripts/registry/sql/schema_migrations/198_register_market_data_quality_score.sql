-- Register the remaining V2.2 Layer 1 quality score after the base
-- direction-neutral taxonomy migration.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'fld_MRMV22013',
  'field',
  'MARKET_DATA_QUALITY_SCORE',
  'field_name',
  '1_data_quality_score',
  NULL,
  'model_01_market_regime;market_context_state;direction_neutral_tradability',
  'registry_only',
  'V2.2 Layer 1 target field for construction coverage, freshness, minimum-history, standardization, and missingness quality evidence.'
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
