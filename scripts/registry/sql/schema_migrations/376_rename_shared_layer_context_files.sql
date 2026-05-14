-- Rename trading-storage shared context CSV files with explicit layer prefixes.

UPDATE trading_registry
SET payload = REPLACE(
        REPLACE(
          REPLACE(payload,
            'market_regime_etf_universe.csv',
            'layer_01_02_market_context_etf_universe.csv'
          ),
          'market_regime_relative_strength_combinations.csv',
          'layer_01_02_market_context_relative_strength_combinations.csv'
        ),
        'target_layer2_context_mapping.csv',
        'layer_02_target_context_mapping.csv'
    ),
    path = REPLACE(
        REPLACE(
          REPLACE(path,
            'market_regime_etf_universe.csv',
            'layer_01_02_market_context_etf_universe.csv'
          ),
          'market_regime_relative_strength_combinations.csv',
          'layer_01_02_market_context_relative_strength_combinations.csv'
        ),
        'target_layer2_context_mapping.csv',
        'layer_02_target_context_mapping.csv'
    ),
    note = REPLACE(
        REPLACE(
          REPLACE(note,
            'market_regime_etf_universe.csv',
            'layer_01_02_market_context_etf_universe.csv'
          ),
          'market_regime_relative_strength_combinations.csv',
          'layer_01_02_market_context_relative_strength_combinations.csv'
        ),
        'target_layer2_context_mapping.csv',
        'layer_02_target_context_mapping.csv'
    ),
    updated_at = NOW()
WHERE payload LIKE '%market_regime_etf_universe.csv%'
   OR payload LIKE '%market_regime_relative_strength_combinations.csv%'
   OR payload LIKE '%target_layer2_context_mapping.csv%'
   OR path LIKE '%market_regime_etf_universe.csv%'
   OR path LIKE '%market_regime_relative_strength_combinations.csv%'
   OR path LIKE '%target_layer2_context_mapping.csv%'
   OR note LIKE '%market_regime_etf_universe.csv%'
   OR note LIKE '%market_regime_relative_strength_combinations.csv%'
   OR note LIKE '%target_layer2_context_mapping.csv%';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'term_LAYERFILE001',
  'term',
  'SHARED_LAYER_PREFIXED_STATIC_FILE_NAMES',
  'text',
  'layer_01_02_market_context_etf_universe.csv;layer_01_02_market_context_relative_strength_combinations.csv;layer_02_target_context_mapping.csv',
  'trading-storage/main/shared/README.md',
  'trading-storage;shared_static_assets;layer_01_market_regime;layer_02_sector_context;target_layer2_context_mapping',
  'sync_artifact',
  'Accepted shared-file naming convention: layer-owned or layer-context files in trading-storage/main/shared use explicit layer prefixes in their filenames. Mixed Layer 1/2 context files use layer_01_02_, while target-to-Layer-2 mapping uses layer_02_.'
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
