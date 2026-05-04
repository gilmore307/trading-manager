-- Register the Layer 3 manager-requested strategy variant simulation feature handoff.
-- trading-manager owns request/orchestration; trading-data owns deterministic
-- per-bar feature production; trading-model owns oracle/lifecycle review.
INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'dki_SVSF001',
    'data_feature',
    'FEATURE_03_STRATEGY_VARIANT_SIMULATION',
    'text',
    'feature_03_strategy_variant_simulation',
    'trading-data/src/data_feature/feature_03_strategy_variant_simulation',
    'trading-data;trading-model;trading-manager;model_03_strategy_selection;strategy_selection_model',
    'sync_artifact',
    'Layer 3 deterministic strategy variant simulation feature surface. trading-manager issues the request, trading-data simulates reviewed family/variant specs per bar for anonymous target candidates, and trading-model consumes the output for oracle construction, variant lifecycle review, agent-reviewed expansion/pruning/promotion, and StrategySelectionModel training evidence.'
  ),
  (
    'trm_SVSR001',
    'term',
    'STRATEGY_VARIANT_SIMULATION_REQUEST',
    'text',
    'strategy_variant_simulation_request',
    'trading-data/docs/04_layer_03_strategy_variant_simulation.md',
    'trading-manager;trading-data;trading-model;feature_03_strategy_variant_simulation;model_03_strategy_selection',
    'registry_only',
    'Manager-issued request for a natural-window deterministic strategy variant simulation run. The request supplies the reviewed time window, anonymous candidate universe reference, strategy variant universe reference, and output target; it does not approve expansion, pruning, or promotion decisions.'
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
