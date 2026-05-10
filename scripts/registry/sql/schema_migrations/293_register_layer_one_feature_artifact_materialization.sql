-- Register offline Layer 1 feed-artifact materialization before feature generation.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_F1MRART001',
    'script',
    'FEATURE_01_MARKET_REGIME_FROM_FEED_ARTIFACTS',
    'command',
    'PYTHONPATH=/root/projects/trading-data/src python3 -m data_feature.feature_01_market_regime.from_feed_artifacts',
    '/root/projects/trading-data/src/data_feature/feature_01_market_regime/from_feed_artifacts.py',
    'trading-data;market_regime_model;feature_01_market_regime;source_01_market_regime;01_feed_alpaca_bars',
    'sync_artifact',
    'Offline manager-runtime bridge for Layer 1: reads already-acquired 01_feed_alpaca_bars equity_bar.csv artifacts, upserts them into trading_data.source_01_market_regime, and generates feature_01_market_regime rows without provider calls.'
  ),
  (
    'cfg_MGRL1FG001',
    'config',
    'MANAGER_LAYER_ONE_FEATURE_FROM_FEED_ARTIFACTS_POLICY',
    'text',
    'layer_01_market_regime.feature_generation materializes reviewed feed artifacts into source_01_market_regime before generating feature_01_market_regime; provider_calls=0; model_activation=false; broker_execution=false',
    'trading-manager/docs/99_historical_scheduler_runtime.md',
    'layer_01_market_regime.feature_generation;feature_01_market_regime;source_01_market_regime;01_feed_alpaca_bars',
    'sync_artifact',
    'Layer 1 feature generation must consume already-acquired local feed artifacts rather than repeating provider calls. The stage may write SQL source/feature rows but must not call providers, activate models, or mutate broker/execution state.'
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
