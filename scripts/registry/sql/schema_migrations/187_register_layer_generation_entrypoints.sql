-- Register stable layer feature/model generation entrypoints used by the
-- control-plane/development workflow. These rows identify callable scripts;
-- importable implementation paths remain owned by data_feature/model terms.
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
    'scr_F1MRGEN',
    'script',
    'FEATURE_01_MARKET_REGIME_GENERATE',
    'command',
    'python3 scripts/generate_feature_01_market_regime.py',
    '/root/projects/trading-data/scripts/generate_feature_01_market_regime.py',
    'trading-data;market_regime_model;feature_01_market_regime;source_01_market_regime',
    'sync_artifact',
    'Stable callable entrypoint for generating Layer 1 MarketRegimeModel deterministic feature rows from accepted source_01_market_regime evidence.'
  ),
  (
    'scr_F2SCGEN',
    'script',
    'FEATURE_02_SECTOR_CONTEXT_GENERATE',
    'command',
    'python3 scripts/generate_feature_02_sector_context.py',
    '/root/projects/trading-data/scripts/generate_feature_02_sector_context.py',
    'trading-data;sector_context_model;feature_02_sector_context;source_01_market_regime',
    'sync_artifact',
    'Stable callable entrypoint for generating Layer 2 SectorContextModel deterministic feature rows. The wrapper calls the importable feature_02_sector_context SQL implementation.'
  ),
  (
    'scr_MRMGEN1',
    'script',
    'MODEL_01_MARKET_REGIME_GENERATE',
    'command',
    'python3 scripts/models/model_01_market_regime/generate_model_01_market_regime.py',
    '/root/projects/trading-model/scripts/models/model_01_market_regime/generate_model_01_market_regime.py',
    'trading-model;market_regime_model;model_01_market_regime;feature_01_market_regime',
    'sync_artifact',
    'Stable callable entrypoint for generating primary MarketRegimeModel output rows and support artifacts from feature_01_market_regime rows.'
  ),
  (
    'scr_SCMGEN1',
    'script',
    'MODEL_02_SECTOR_CONTEXT_GENERATE',
    'command',
    'python3 scripts/models/model_02_sector_context/generate_model_02_sector_context.py',
    '/root/projects/trading-model/scripts/models/model_02_sector_context/generate_model_02_sector_context.py',
    'trading-model;sector_context_model;model_02_sector_context;feature_02_sector_context;model_01_market_regime',
    'sync_artifact',
    'Stable callable entrypoint for generating primary SectorContextModel output rows and support artifacts from feature_02_sector_context rows plus market-regime context.'
  ),
  (
    'scr_MRMSMOKE',
    'script',
    'MODEL_01_MARKET_REGIME_DEVELOPMENT_SMOKE',
    'command',
    'python3 scripts/models/model_01_market_regime/run_market_regime_development_smoke.py',
    '/root/projects/trading-model/scripts/models/model_01_market_regime/run_market_regime_development_smoke.py',
    'trading-model;market_regime_model;model_01_market_regime;development_smoke;model_evaluation',
    'sync_artifact',
    'Stable callable development smoke entrypoint for the Layer 1 source-to-feature-to-model-to-evaluation path. It calls no providers and cleans development tables by default.'
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
