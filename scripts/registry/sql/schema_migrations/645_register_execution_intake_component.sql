-- Register narrowed C01 execution intake boundary.

UPDATE trading_registry
SET payload = replace(payload, 'component_01_allocation', 'component_01_intake'),
    applies_to = replace(applies_to, 'component_01_allocation', 'component_01_intake'),
    note = replace(note, 'component_01_allocation', 'component_01_intake'),
    updated_at = CURRENT_TIMESTAMP
WHERE payload LIKE '%component_01_allocation%'
   OR applies_to LIKE '%component_01_allocation%'
   OR note LIKE '%component_01_allocation%';

UPDATE trading_registry
SET payload = replace(payload, 'target_allocation_snapshot', 'execution_intake_snapshot'),
    note = replace(note, 'target_allocation_snapshot', 'execution_intake_snapshot'),
    updated_at = CURRENT_TIMESTAMP
WHERE payload LIKE '%target_allocation_snapshot%'
   OR note LIKE '%target_allocation_snapshot%';

UPDATE trading_registry
SET payload = replace(payload, 'C01 Allocation', 'C01 Intake'),
    note = replace(note, 'C01 Allocation', 'C01 Intake'),
    updated_at = CURRENT_TIMESTAMP
WHERE payload LIKE '%C01 Allocation%'
   OR note LIKE '%C01 Allocation%';

UPDATE trading_registry
SET key = 'EXECUTION_INTAKE_SNAPSHOT',
    payload = 'execution_intake_snapshot',
    applies_to = 'trading-execution;component_01_intake;live;replay',
    note = 'Execution runtime contract emitted by C01 Intake for account balance state, current holdings, watch targets, and account-sleeve candidate filtering. It does not allocate risk budget, size positions, decide entries, manage exits, construct orders, or mutate broker/account state.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'art_EXECRTC003';

UPDATE trading_registry
SET payload = 'C01 Intake=component_01_intake;C02 Entry=component_02_entry;C03 Lifecycle=component_03_lifecycle;C04 Option Review=component_04_option_review;C05 Failure Review=component_05_failure_review;C06 Order Intent=component_06_order_intent;C07 Execution Gate=component_07_execution_gate',
    note = 'Accepted concise numbered intraday execution component sequence. C01 Intake owns account/watch-target intake only; downstream components own entry, lifecycle, risk, option review, order intent, and execution gates. component_id values follow the model-aligned physical naming pattern component_01_* through component_07_*.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_EXECRTC003';

UPDATE trading_registry
SET payload = 'same_components_live_and_replay_different_adapters;evaluation_calls_execution_graph;numbered_intraday_component_sequence_c01_c07;model_aligned_component_id_sequence;c01_intake_no_risk_allocation;layer10_failure_explanation_only;components_emit_broker_neutral_decisions;separate_crypto_and_equity_options_accounts;no_cross_account_netting;fixed_crypto_pool_btc_eth_sol',
    note = 'Policy stating live trading and Replay use the same execution component graph and decision contracts, with only adapter profiles swapped. C01 Intake reads account state, current holdings, and watch targets only; it does not allocate risk budget or manage positions. trading-evaluation owns orchestration and judgment, not duplicated trading decisions. Runtime decisions must keep crypto and equity/options in independent account sleeves without cross-account collateral, buying-power, position, or risk-budget netting.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_EXECRTC001';
