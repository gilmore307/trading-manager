-- Register manager-owned Layer 2 sector-context historical-training batch preparation.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_L2HT001',
    'term',
    'LAYER_TWO_HISTORICAL_TRAINING_BATCH',
    'text',
    'layer_02_sector_context_historical_training_v1',
    'trading-manager/docs/94_monthly_backfill.md',
    'layer_02_sector_context;sector_context_model;monthly_backfill_v1;manager_request_v1;historical_training',
    'sync_artifact',
    'Manager-owned historical-training preparation phase for Layer 2 SectorContextModel. It expands the reviewed sector/industry ETF universe into component requests and handoff payloads without provider dispatch, model activation, or broker execution.'
  ),
  (
    'scr_L2HT001',
    'script',
    'MANAGER_PREPARE_LAYER_TWO_HISTORICAL_TRAINING',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/prepare_layer_two_historical_training.py',
    '/root/projects/trading-manager/scripts/tasks/prepare_layer_two_historical_training.py',
    'layer_02_sector_context_historical_training_v1;sector_context_model;manager_request_v1;request_payload;request_handoff;live_call_approval_required',
    'sync_artifact',
    'Callable manager entrypoint that prepares a Layer 2 historical-training batch by planning the full sector/industry ETF universe, materializing task-key payloads, and validating dry-run handoff boundaries without calling providers.'
  ),
  (
    'cfg_L2HT001',
    'config',
    'LAYER_TWO_HISTORICAL_TRAINING_REQUEST_COUNT',
    'text',
    '25 approval-gated Alpaca bar requests for the reviewed layer_02_sector_context sector/industry ETF universe at 2016-01.',
    'trading-storage/main/shared/market_regime_etf_universe.csv',
    'layer_02_sector_context;01_feed_alpaca_bars;manager_request_v1;live_call_approval_required',
    'sync_artifact',
    'Layer 2 data acquisition uses the reviewed layer_02_sector_context rows from the shared ETF universe. Preparing task keys is offline; provider dispatch still requires live_call_approval_v1.'
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
