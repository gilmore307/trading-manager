-- Correct Shadow runtime component numbering from S01 to C08.

UPDATE trading_registry
SET applies_to = 'trading-execution;runtime_model_lifecycle;c08_shadow_runtime_component;market_hours;active_shadow_model_group_comparison',
    note = 'Execution-owned C08 intraday Shadow component. It runs the active model group and eligible promoted shadow model groups over realtime market-hours snapshots, records comparable evidence, and feeds mature evidence into execution_shadow_cycle_selection. It is not used by promotion Replay and has no broker/order/account or active-pointer mutation authority.',
    updated_at = NOW()
WHERE id = 'art_EXECSHADOW001';

UPDATE trading_registry
SET applies_to = 'trading-execution;runtime_model_lifecycle;c08_shadow_runtime_component;realtime_model_decision_effectiveness',
    note = 'Evidence emitted by C08 Model Group Shadow Comparison from realtime market-hours active/shadow model-group runs. It may support later runtime roster selection but cannot authorize orders, active pointer writes, broker calls, or account mutation.',
    updated_at = NOW()
WHERE id = 'art_EXECSHADOW002';

UPDATE trading_registry
SET payload = 'c08_model_group_shadow_comparison_intraday_component;realtime_data_only;already_promoted_model_groups_only;not_replay;active_model_only_trading_authority;capacity_gated',
    applies_to = 'trading-execution;runtime_model_lifecycle;c08_shadow_runtime_component;execution_shadow_cycle_selection',
    note = 'C08 Model Group Shadow Comparison is a market-hours realtime component for comparing the active model group with eligible already-promoted shadow model groups. Shadow outputs are evidence only; only the current active model can route decisions into live C01-C06 trading authority until an execution_active_model_config_write gate changes the pointer. C08 must be capacity-gated so shadow comparison does not degrade C01-C06 latency, market-data ingestion, broker gates, or account-state freshness.',
    updated_at = NOW()
WHERE id = 'cfg_SHADOWS01001';
