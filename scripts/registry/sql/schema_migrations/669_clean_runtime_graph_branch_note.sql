-- Clean the runtime graph artifact note after registering C01 branch paths.

UPDATE trading_registry
SET note = 'Execution-owned runtime component graph used by both live trading and Replay. The graph includes component_sequence as the stable C01-C07 component catalog and execution_paths for the accepted branches: C01 candidate_entry_pool routes to C02, C01 open_position_pool routes to C03, and accepted C02/C03 intents converge at C04 before C05/C06. trading-evaluation calls this graph for Replay decisions, then owns settlement, metrics, and promotion evidence.',
    updated_at = NOW()
WHERE key = 'EXECUTION_RUNTIME_COMPONENT_GRAPH';
