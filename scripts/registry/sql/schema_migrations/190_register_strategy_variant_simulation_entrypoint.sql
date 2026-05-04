-- Register the stable callable entrypoint for Layer 3 strategy variant simulation.
INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_F3SVSIM',
    'script',
    'FEATURE_03_STRATEGY_VARIANT_SIMULATION_GENERATE',
    'command',
    'python3 scripts/generate_feature_03_strategy_variant_simulation.py',
    '/root/projects/trading-data/scripts/generate_feature_03_strategy_variant_simulation.py',
    'trading-data;trading-manager;trading-model;feature_03_strategy_variant_simulation;model_03_strategy_selection',
    'sync_artifact',
    'Stable callable entrypoint for manager-requested Layer 3 deterministic strategy variant simulation. The wrapper calls the importable feature_03_strategy_variant_simulation SQL implementation and writes simulation features for downstream StrategySelectionModel oracle/lifecycle review.'
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
