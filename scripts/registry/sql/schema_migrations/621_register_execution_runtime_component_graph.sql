-- Register the execution-owned runtime component graph shared by live trading
-- and Replay. Historical migrations keep older replay wording as audit
-- evidence, but the active registry snapshot should expose only the current
-- names.

UPDATE trading_registry
SET payload = replace(replace(replace(payload, 'replay_replay', 'replay'), 'Replay Replay', 'Replay'), 'replay replay', 'replay'),
    path = replace(replace(replace(path, 'replay_replay', 'replay'), 'Replay Replay', 'Replay'), 'replay replay', 'replay'),
    applies_to = replace(replace(replace(applies_to, 'replay_replay', 'replay'), 'Replay Replay', 'Replay'), 'replay replay', 'replay'),
    note = replace(replace(replace(replace(note, 'replay_replay', 'replay'), 'Replay Replay', 'Replay'), 'replay replay', 'replay'), 'replay/replay', 'replay'),
    updated_at = NOW()
WHERE payload ILIKE '%replay_replay%'
   OR path ILIKE '%replay_replay%'
   OR applies_to ILIKE '%replay_replay%'
   OR note ILIKE '%replay_replay%'
   OR note ILIKE '%replay replay%'
   OR note ILIKE '%replay/replay%';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_EXECRTC001',
    'artifact_type',
    'EXECUTION_RUNTIME_COMPONENT',
    'text',
    'execution_runtime_component',
    'trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/components.py',
    'trading-execution;runtime_component;live;replay;decision_graph',
    'sync_artifact',
    'Task-level execution runtime component contract shared by live trading and Replay. Components call frozen model outputs as inputs, but execution owns trading lifecycle decisions.'
  ),
  (
    'art_EXECRTC002',
    'artifact_type',
    'EXECUTION_RUNTIME_COMPONENT_GRAPH',
    'text',
    'execution_runtime_component_graph',
    'trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/components.py',
    'trading-execution;runtime_component_graph;live;replay;trading-evaluation',
    'sync_artifact',
    'Execution-owned runtime component graph used by both live trading and Replay. trading-evaluation calls this graph for Replay decisions, then owns settlement, metrics, and promotion evidence.'
  ),
  (
    'art_EXECRTC003',
    'artifact_type',
    'TARGET_ALLOCATION_SNAPSHOT',
    'text',
    'target_allocation_snapshot',
    'trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/components.py',
    'trading-execution;opportunity_risk_allocation_engine;live;replay',
    'sync_artifact',
    'Execution runtime contract emitted by the Opportunity & Risk Allocation Engine for selected targets, account-aware risk budget, and current target-pool monitoring.'
  ),
  (
    'art_EXECRTC004',
    'artifact_type',
    'ENTRY_DECISION',
    'text',
    'entry_decision',
    'trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/components.py',
    'trading-execution;entry_decision_engine;live;replay',
    'sync_artifact',
    'Execution runtime contract deciding open, watch-only, defer, or block for an allocated target. Entry uses Layer 4 for forward event risk and does not call Layer 10.'
  ),
  (
    'art_EXECRTC005',
    'artifact_type',
    'POSITION_LIFECYCLE_DECISION',
    'text',
    'position_lifecycle_decision',
    'trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/components.py',
    'trading-execution;position_lifecycle_controller;live;replay',
    'sync_artifact',
    'Execution runtime contract for hold, add, reduce, exit, stop, take-profit, or flatten-review decisions on existing positions.'
  ),
  (
    'art_EXECRTC006',
    'artifact_type',
    'OPTION_REEXPRESSION_DECISION',
    'text',
    'option_reexpression_decision',
    'trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/components.py',
    'trading-execution;option_reexpression_review;live;replay',
    'sync_artifact',
    'Execution runtime contract for periodically reviewing held option contracts and rolling when a replacement contract is materially better after cost, liquidity, Greek, DTE, and risk checks.'
  ),
  (
    'art_EXECRTC007',
    'artifact_type',
    'FAILURE_EXPLANATION_PACKET',
    'text',
    'failure_explanation_packet',
    'trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/components.py',
    'trading-execution;failure_explanation_component;layer_10_event_risk_governor;live;replay',
    'sync_artifact',
    'Execution runtime contract produced only after observed model or trade failure. Layer 10 links failure evidence to possible unscreened events and emits Layer 4 feedback candidates.'
  ),
  (
    'art_EXECRTC008',
    'artifact_type',
    'EXECUTION_ORDER_INTENT',
    'text',
    'execution_order_intent',
    'trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/components.py',
    'trading-execution;order_intent_builder;live;replay',
    'sync_artifact',
    'Broker-neutral execution intent emitted from accepted entry, lifecycle, or option re-expression decisions before any live broker/account mutation gate.'
  ),
  (
    'art_EXECRTC009',
    'artifact_type',
    'SIMULATED_FILL_EVENT',
    'text',
    'simulated_fill_event',
    'trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/components.py',
    'trading-execution;execution_gate_adapter;replay;fill_simulator',
    'sync_artifact',
    'Replay-only fill simulator event emitted from execution order intents. It never mutates a real broker or account.'
  ),
  (
    'cfg_EXECRTC001',
    'config',
    'EXECUTION_RUNTIME_COMPONENT_GRAPH_POLICY',
    'text',
    'same_components_live_and_replay_different_adapters;evaluation_calls_execution_graph;layer10_failure_explanation_only;components_emit_broker_neutral_decisions',
    'trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/components.py',
    'trading-execution;trading-evaluation;runtime_component_graph;live;replay',
    'sync_artifact',
    'Policy stating live trading and Replay use the same execution component graph and decision contracts, with only adapter profiles swapped. trading-evaluation owns orchestration and judgment, not duplicated trading decisions.'
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
