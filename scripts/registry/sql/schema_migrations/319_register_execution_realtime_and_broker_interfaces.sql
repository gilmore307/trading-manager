-- Register initial trading-execution realtime data and broker interface catalogs.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_EXEC_RT001',
    'term',
    'EXECUTION_REALTIME_DATA_INTERFACE',
    'text',
    'execution_realtime_data_interface_v1',
    'trading-execution/src/trading_execution/market_data/contracts.py',
    'trading-execution;realtime_market_data;execution_runtime;okx;alpaca;thetadata',
    'sync_artifact',
    'Execution-side realtime market-data interface catalog. Realtime routes may share canonical providers with historical data, but use distinct realtime transports such as WebSocket streams or realtime HTTP snapshots.'
  ),
  (
    'trm_EXEC_BRK001',
    'term',
    'EXECUTION_BROKER_INTERFACE',
    'text',
    'execution_broker_interface_v1',
    'trading-execution/src/trading_execution/broker/contracts.py',
    'trading-execution;broker_interface;exchange_interface;execution_runtime;okx;firstrade',
    'sync_artifact',
    'Execution broker/exchange interface catalog. OKX is accepted for crypto adapter scaffolding with live mutation disabled; Firstrade is recorded as deferred because no official trading API is accepted.'
  ),
  (
    'trm_EXEC_CAP001',
    'artifact_type',
    'EXECUTION_CAPABILITY_CATALOG',
    'text',
    'execution_capability_catalog_v1',
    'trading-execution/src/trading_execution/broker/contracts.py',
    'trading-execution;execution_realtime_data_interface_v1;execution_broker_interface_v1;capability_catalog',
    'sync_artifact',
    'Side-effect-free catalog combining reviewed realtime data interfaces and broker interfaces. It records that provider calls, broker calls, and order mutation are not performed by catalog inspection.'
  ),
  (
    'scr_EXEC_CAP001',
    'script',
    'EXECUTION_CAPABILITY_CATALOG_LIST',
    'command',
    'PYTHONPATH=src python3 scripts/execution/list_execution_capabilities.py',
    'trading-execution/scripts/execution/list_execution_capabilities.py',
    'trading-execution;execution_capability_catalog_v1;inspection;no_provider_calls;no_broker_calls',
    'sync_artifact',
    'Prints the execution capability catalog without external calls, order construction, broker mutation, provider streams, model activation, or storage lifecycle mutation.'
  ),
  (
    'cfg_EXEC_OKX001',
    'config',
    'EXECUTION_OKX_CRYPTO_BROKER_POLICY',
    'text',
    'okx_official_api_adapter_scaffold_allowed_live_order_mutation_disabled',
    'trading-execution/docs/10_broker_interfaces.md',
    'trading-execution;okx;crypto_order_execution;trade_risk_cap;execution_mode;idempotency',
    'sync_artifact',
    'OKX is the accepted crypto broker/exchange interface candidate because an official API exists. Initial work may validate/simulate only; live order mutation remains disabled until explicit gates exist.'
  ),
  (
    'cfg_EXEC_FT001',
    'config',
    'EXECUTION_FIRSTRADE_DEFERRED_POLICY',
    'text',
    'firstrade_deferred_no_official_trading_api_do_not_automate_reverse_engineered_order_flow',
    'trading-execution/docs/10_broker_interfaces.md',
    'trading-execution;firstrade;us_equity;us_option;deferred;no_official_api',
    'sync_artifact',
    'Firstrade remains intended for US equity/options execution, but automation is deferred because no accepted official trading API exists. Reverse-engineered login, browser trading, and scraped order-ticket automation are not accepted.'
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
