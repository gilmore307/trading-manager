-- Register the hard boundary between promotion Replay and runtime Shadow.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_RPSHADOW001',
    'config',
    'REPLAY_SHADOW_SEPARATION_POLICY',
    'text',
    'replay_fixed_historical_evaluation_not_shadow_selection;shadow_realtime_promoted_model_selection_not_training_output_evaluation',
    'trading-evaluation/docs/20_replay_contracts.md;trading-evaluation/docs/05_decision.md;trading-execution/docs/40_runtime_model_lifecycle.md',
    'trading-evaluation;promotion_replay;trading-execution;runtime_model_lifecycle;execution_shadow_cycle_selection',
    'sync_artifact',
    'Replay uses a fixed historical window and frozen historical data to evaluate whether a training output deserves promotion readiness. Shadow uses realtime market-hours evidence to compare already-promoted models and select active/realtime/shadow/eliminate runtime roles. Promotion Replay must not call execution_shadow_cycle_selection.'
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

UPDATE trading_registry
SET note = 'Execution policy for runtime model lifecycle: active model remains trading authority, promoted candidates run shadow on realtime market-hours data, mature cycle evidence is reviewed with anonymous model labels, and the active config pointer write requires a separate audited gate. This is distinct from promotion Replay, which uses fixed historical data and must not call execution_shadow_cycle_selection.',
    updated_at = NOW()
WHERE key = 'EXECUTION_RUNTIME_MODEL_LIFECYCLE_POLICY';

UPDATE trading_registry
SET note = 'Policy stating live trading and Replay use the same execution component graph and decision contracts, with only adapter profiles swapped. Replay is a fixed historical evaluation mechanism for training outputs, while shadow is a realtime execution-owned selection mechanism for already-promoted models. Runtime decisions must keep crypto and equity/options in independent account sleeves without cross-account collateral, buying-power, position, or risk-budget netting.',
    updated_at = NOW()
WHERE key = 'EXECUTION_RUNTIME_COMPONENT_GRAPH_POLICY';
