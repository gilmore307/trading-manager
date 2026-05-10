-- Register Layer 2 feed-artifact materialization before sector-context feature generation.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_F2SCART001',
    'script',
    'FEATURE_02_SECTOR_CONTEXT_FROM_FEED_ARTIFACTS',
    'command',
    'PYTHONPATH=/root/projects/trading-data/src python3 -m data_feature.feature_02_sector_context.from_feed_artifacts',
    '/root/projects/trading-data/src/data_feature/feature_02_sector_context/from_feed_artifacts.py',
    'trading-data;layer_02_sector_context;feature_02_sector_context;source_01_market_regime;01_feed_alpaca_bars',
    'sync_artifact',
    'Offline manager-runtime bridge for Layer 2: reads already-acquired 01_feed_alpaca_bars equity_bar.csv artifacts, upserts them into trading_data.source_01_market_regime, and generates feature_02_sector_context rows without provider calls.'
  ),
  (
    'cfg_MGRL2FG001',
    'config',
    'MANAGER_LAYER_TWO_FEATURE_FROM_FEED_ARTIFACTS_POLICY',
    'text',
    'layer_02_sector_context.feature_generation materializes reviewed feed artifacts into source_01_market_regime before generating feature_02_sector_context; provider_calls=0; model_activation=false; broker_execution=false',
    'trading-manager/docs/99_historical_scheduler_runtime.md',
    'layer_02_sector_context.feature_generation;feature_02_sector_context;source_01_market_regime;01_feed_alpaca_bars',
    'sync_artifact',
    'Layer 2 feature generation must consume already-acquired local feed artifacts rather than repeating provider calls. The stage may write SQL source/feature rows but must not call providers, activate models, or mutate broker/execution state.'
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
