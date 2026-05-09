-- Register manager-owned Layer 1 historical-training batch preparation.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_L1HT001',
    'term',
    'LAYER_ONE_HISTORICAL_TRAINING_BATCH',
    'text',
    'layer_01_market_regime_historical_training_v1',
    'trading-manager/docs/94_monthly_backfill.md',
    'layer_01_market_regime;market_regime_model;monthly_backfill_v1;manager_request_v1;historical_training',
    'sync_artifact',
    'Manager-owned historical-training preparation phase for Layer 1 MarketRegimeModel. It expands the reviewed Layer 1 ETF universe into component requests and handoff payloads without provider dispatch, model activation, or broker execution.'
  ),
  (
    'scr_L1HT001',
    'script',
    'MANAGER_PREPARE_LAYER_ONE_HISTORICAL_TRAINING',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/prepare_layer_one_historical_training.py',
    '/root/projects/trading-manager/scripts/tasks/prepare_layer_one_historical_training.py',
    'layer_01_market_regime_historical_training_v1;market_regime_model;manager_request_v1;request_payload;request_handoff;live_call_approval_required',
    'sync_artifact',
    'Callable manager entrypoint that prepares a Layer 1 historical-training batch by planning full market-regime ETF universe requests, materializing task-key payloads, and validating dry-run handoff boundaries without calling providers.'
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
