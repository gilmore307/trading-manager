-- Register concise numbered execution runtime component sequence.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'cfg_EXECRTC003',
  'config',
  'EXECUTION_RUNTIME_COMPONENT_SEQUENCE',
  'text',
  'C01 Allocation=opportunity_risk_allocation_engine;C02 Entry=entry_decision_engine;C03 Lifecycle=position_lifecycle_controller;C04 Option Review=option_reexpression_review;C05 Failure Review=failure_explanation_component;C06 Order Intent=order_intent_builder;C07 Execution Gate=execution_gate_adapter',
  'trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/components.py',
  'trading-execution;runtime_component_graph;live;replay;intraday_flow_order',
  'sync_artifact',
  'Accepted concise numbered intraday execution component sequence. component_step/component_name are display and ordering fields; stable component_id values remain the contract-facing interface names.'
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

UPDATE trading_registry
SET payload = 'same_components_live_and_replay_different_adapters;evaluation_calls_execution_graph;numbered_intraday_component_sequence_c01_c07;component_step_and_short_name_fields;layer10_failure_explanation_only;components_emit_broker_neutral_decisions;separate_crypto_and_equity_options_accounts;no_cross_account_netting;fixed_crypto_pool_btc_eth_sol',
    note = 'Policy stating live trading and Replay use the same execution component graph and decision contracts, with only adapter profiles swapped. Runtime components expose concise numbered intraday steps C01-C07 while retaining stable component_id contract names. trading-evaluation owns orchestration and judgment, not duplicated trading decisions. Runtime decisions must keep crypto and equity/options in independent account sleeves without cross-account collateral, buying-power, position, or risk-budget netting.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_EXECRTC001';

UPDATE trading_registry
SET note = 'Task-level execution runtime component contract shared by live trading and Replay. Components expose component_step and component_name for concise intraday ordering while retaining stable component_id values. Components call frozen model outputs as inputs, but execution owns trading lifecycle decisions.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'art_EXECRTC001';

UPDATE trading_registry
SET note = 'Execution-owned runtime component graph used by both live trading and Replay. The graph includes component_sequence for C01-C07 intraday ordering. trading-evaluation calls this graph for Replay decisions, then owns settlement, metrics, and promotion evidence.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'art_EXECRTC002';
