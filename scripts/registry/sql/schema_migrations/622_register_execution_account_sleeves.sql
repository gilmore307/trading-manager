-- Register execution account sleeves for separate crypto and equity/options
-- runtime accounts.

UPDATE trading_registry
SET payload = 'same_components_live_and_replay_different_adapters;evaluation_calls_execution_graph;layer10_failure_explanation_only;components_emit_broker_neutral_decisions;separate_crypto_and_equity_options_accounts;no_cross_account_netting;fixed_crypto_pool_btc_eth_sol',
    note = 'Policy stating live trading and Replay use the same execution component graph and decision contracts, with only adapter profiles swapped. trading-evaluation owns orchestration and judgment, not duplicated trading decisions. Runtime decisions must keep crypto and equity/options in independent account sleeves without cross-account collateral, buying-power, position, or risk-budget netting.',
    updated_at = NOW()
WHERE key = 'EXECUTION_RUNTIME_COMPONENT_GRAPH_POLICY';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_EXECRTC010',
    'artifact_type',
    'EXECUTION_ACCOUNT_SLEEVE',
    'text',
    'execution_account_sleeve',
    'trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/components.py',
    'trading-execution;runtime_component_graph;account_sleeve;live;replay',
    'sync_artifact',
    'Execution runtime contract for independently funded account sleeves. Every target allocation, entry decision, position lifecycle decision, option re-expression decision, and execution order intent belongs to exactly one sleeve.'
  ),
  (
    'term_EXECRTC001',
    'term',
    'CRYPTO_SPOT_ACCOUNT_SLEEVE',
    'text',
    'crypto_spot_account',
    'trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/components.py',
    'trading-execution;account_sleeve;crypto_spot;okx;live;replay',
    'sync_artifact',
    'Independent crypto spot execution account sleeve. It uses crypto_account_state_snapshot and crypto_risk_budget_snapshot, allows crypto_spot assets only, and starts from the fixed BTC, ETH, and SOL candidate pool.'
  ),
  (
    'term_EXECRTC002',
    'term',
    'EQUITY_OPTIONS_ACCOUNT_SLEEVE',
    'text',
    'equity_options_account',
    'trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/components.py',
    'trading-execution;account_sleeve;us_equity;us_etf;us_option;live;replay',
    'sync_artifact',
    'Independent US equity/options execution account sleeve. It uses equity_options_account_state_snapshot and equity_options_risk_budget_snapshot, follows the reviewed stock and optionable-underlying candidate process, and enables option re-expression.'
  ),
  (
    'cfg_EXECRTC002',
    'config',
    'CRYPTO_SPOT_CANDIDATE_POOL_POLICY',
    'text',
    'fixed_crypto_spot_pool_btc_eth_sol;symbols=BTC,ETH,SOL;okx_spot_instruments=BTC-USDT,ETH-USDT,SOL-USDT',
    'trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/components.py',
    'trading-execution;crypto_spot_account;candidate_pool;okx',
    'sync_artifact',
    'Accepted initial crypto candidate pool for execution runtime. Crypto spot scanning is limited to BTC, ETH, and SOL, with OKX spot instrument refs BTC-USDT, ETH-USDT, and SOL-USDT.'
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
    updated_at = NOW();
