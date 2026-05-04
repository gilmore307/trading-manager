-- Rename the Layer 3 data-feature handoff to match the accepted layer name.
-- Variant simulation is an action inside feature_03_strategy_selection, not the
-- feature-level identifier.
DELETE FROM trading_registry
WHERE id IN ('dki_SVSF001', 'scr_F3SVSIM', 'trm_SVSR001');

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'dki_SSFE001',
    'data_feature',
    'FEATURE_03_STRATEGY_SELECTION',
    'text',
    'feature_03_strategy_selection',
    'trading-data/src/data_feature/feature_03_strategy_selection',
    'trading-data;trading-model;trading-manager;model_03_strategy_selection;strategy_selection_model',
    'sync_artifact',
    'Layer 3 deterministic StrategySelectionModel feature surface. trading-manager issues the request, trading-data simulates reviewed strategy family/variant specs per bar under feature_03_strategy_selection, and trading-model consumes the output for oracle construction, variant lifecycle review, agent-reviewed expansion/pruning/promotion, and StrategySelectionModel training evidence.'
  ),
  (
    'trm_SSFR001',
    'term',
    'STRATEGY_SELECTION_FEATURE_REQUEST',
    'text',
    'strategy_selection_feature_request',
    'trading-data/docs/04_layer_03_strategy_selection.md',
    'trading-manager;trading-data;trading-model;feature_03_strategy_selection;model_03_strategy_selection',
    'registry_only',
    'Manager-issued request for a natural-window deterministic StrategySelectionModel feature run. The request supplies the reviewed time window, anonymous candidate universe reference, strategy variant universe reference, and output target; it does not approve expansion, pruning, or promotion decisions.'
  ),
  (
    'scr_F3SSGEN',
    'script',
    'FEATURE_03_STRATEGY_SELECTION_GENERATE',
    'command',
    'python3 scripts/generate_feature_03_strategy_selection.py',
    '/root/projects/trading-data/scripts/generate_feature_03_strategy_selection.py',
    'trading-data;trading-manager;trading-model;feature_03_strategy_selection;model_03_strategy_selection',
    'sync_artifact',
    'Stable callable entrypoint for manager-requested Layer 3 deterministic strategy selection feature generation. The wrapper calls the importable feature_03_strategy_selection SQL implementation and writes variant simulation features for downstream StrategySelectionModel oracle/lifecycle review.'
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
