-- Register execution-owned realtime monitor loop receipt and entrypoint.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_EXEC_RT_MONITOR002',
    'script',
    'EXECUTION_REALTIME_MONITOR_LOOP',
    'text',
    'PYTHONPATH=src python3 scripts/execution/run_realtime_monitor_loop.py',
    'trading-execution/scripts/execution/run_realtime_monitor_loop.py',
    'trading-execution;realtime_monitoring;runtime_loop;alpaca;etf_universe;read_only_live_observe;no_model_activation;no_order_construction;no_account_mutation',
    'sync_artifact',
    'Execution-owned bounded realtime monitor loop. Repeats read-only monitor smoke cycles, writes per-cycle receipts plus loop_receipt.json, and requires --execute-live-observe before provider calls.'
  ),
  (
    'trm_EXEC_RT_MONITOR002',
    'term',
    'EXECUTION_REALTIME_MONITOR_LOOP_RECEIPT',
    'text',
    'execution_realtime_monitor_loop_receipt_v1',
    'trading-execution/src/trading_execution/market_data/realtime_monitor.py',
    'trading-execution;realtime_monitoring;runtime_loop;cycle_receipts;provider_status_summary;safety_invariants',
    'sync_artifact',
    'Loop-level receipt for supervised execution-owned realtime monitoring. Aggregates per-cycle provider calls, cycle status, receipt paths, and invariant flags while leaving manager as evidence consumer only.'
  ),
  (
    'trm_EXEC_RT_MONITOR003',
    'term',
    'EXECUTION_REALTIME_MONITOR_CYCLE_SUMMARY',
    'text',
    'execution_realtime_monitor_cycle_summary_v1',
    'trading-execution/src/trading_execution/market_data/realtime_monitor.py',
    'trading-execution;realtime_monitoring;runtime_loop;cycle_summary;reconnect_backoff_observability',
    'sync_artifact',
    'Per-cycle monitor summary with request/approval ids, provider observation summary, cycle status, timing, and next-cycle delay for reconnect/backoff observability.'
  ),
  (
    'cfg_EXEC_RT_MONITOR002',
    'config',
    'EXECUTION_REALTIME_MONITOR_CONTROL_BOUNDARY',
    'text',
    'execution_owns_monitor_process_lifecycle_reconnect_backoff_throttle_and_receipts;manager_consumes_evidence_only;no_broker_or_account_mutation',
    'trading-execution/docs/09_realtime_data.md',
    'trading-execution;trading-manager;realtime_monitoring;runtime_boundary;manager_evidence_consumer_only',
    'sync_artifact',
    'Realtime monitor control boundary: trading-execution owns runtime lifecycle and receipts; trading-manager may consume evidence but must not control monitor processes or broker/account mutation.'
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
