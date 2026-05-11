-- Register execution-owned realtime monitor smoke entrypoint.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_EXEC_RT_MONITOR001',
    'script',
    'EXECUTION_REALTIME_MONITOR_SMOKE',
    'text',
    'PYTHONPATH=src python3 scripts/execution/run_realtime_monitor_smoke.py',
    'trading-execution/scripts/execution/run_realtime_monitor_smoke.py',
    'trading-execution;realtime_monitoring;alpaca;etf_universe;read_only_live_observe;no_model_activation;no_order_construction;no_account_mutation',
    'sync_artifact',
    'Execution-owned bounded realtime monitor smoke for the reviewed Layer 1/2 ETF universe. Requires --execute-live-observe before provider calls and emits execution_realtime_monitor_smoke_receipt_v1.'
  ),
  (
    'trm_EXEC_RT_MONITOR001',
    'term',
    'EXECUTION_REALTIME_MONITOR_SMOKE_RECEIPT',
    'text',
    'execution_realtime_monitor_smoke_receipt_v1',
    'trading-execution/src/trading_execution/market_data/realtime_monitor.py',
    'trading-execution;realtime_monitoring;runtime_smoke;receipt;provider_status_summary;safety_invariants',
    'sync_artifact',
    'Receipt envelope for a bounded execution-owned realtime monitor smoke. Includes request, approval, live-observe result, and a credential-free summary of provider calls, observations, capture counts, and invariant flags.'
  ),
  (
    'cfg_EXEC_RT_MONITOR001',
    'config',
    'EXECUTION_REALTIME_MONITOR_INITIAL_UNIVERSE_POLICY',
    'text',
    'use_reviewed_layer_01_and_layer_02_etf_universe_for_initial_alpaca_snapshot_smoke;no_holdings_wide_high_frequency_monitoring_by_default',
    'trading-execution/docs/09_realtime_data.md',
    'trading-execution;realtime_monitoring;market_regime_etf_universe;layer_01_market_regime;layer_02_sector_context;capacity_policy',
    'sync_artifact',
    'Initial realtime monitor universe policy: smoke the reviewed 47-symbol Layer 1/2 ETF universe only; do not expand to full holdings-wide high-frequency monitoring by default.'
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
