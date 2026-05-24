-- Align execution component ids with model physical naming.

WITH component_name_map(old_name, new_name) AS (
  VALUES
    ('opportunity_risk_allocation_engine', 'component_01_allocation'),
    ('entry_decision_engine', 'component_02_entry'),
    ('position_lifecycle_controller', 'component_03_lifecycle'),
    ('option_reexpression_review', 'component_04_option_review'),
    ('failure_explanation_component', 'component_05_failure_review'),
    ('order_intent_builder', 'component_06_order_intent'),
    ('execution_gate_adapter', 'component_07_execution_gate')
)
UPDATE trading_registry
SET payload = replace(payload, old_name, new_name),
    applies_to = replace(applies_to, old_name, new_name),
    note = replace(note, old_name, new_name),
    updated_at = CURRENT_TIMESTAMP
FROM component_name_map
WHERE payload LIKE '%' || old_name || '%'
   OR applies_to LIKE '%' || old_name || '%'
   OR note LIKE '%' || old_name || '%';

UPDATE trading_registry
SET payload = 'C01 Allocation=component_01_allocation;C02 Entry=component_02_entry;C03 Lifecycle=component_03_lifecycle;C04 Option Review=component_04_option_review;C05 Failure Review=component_05_failure_review;C06 Order Intent=component_06_order_intent;C07 Execution Gate=component_07_execution_gate',
    note = 'Accepted concise numbered intraday execution component sequence. component_step/component_name are display and ordering fields; stable component_id values follow the model-aligned physical naming pattern component_01_* through component_07_*.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_EXECRTC003';

UPDATE trading_registry
SET payload = 'same_components_live_and_replay_different_adapters;evaluation_calls_execution_graph;numbered_intraday_component_sequence_c01_c07;model_aligned_component_id_sequence;layer10_failure_explanation_only;components_emit_broker_neutral_decisions;separate_crypto_and_equity_options_accounts;no_cross_account_netting;fixed_crypto_pool_btc_eth_sol',
    note = 'Policy stating live trading and Replay use the same execution component graph and decision contracts, with only adapter profiles swapped. Runtime components expose concise numbered intraday steps C01-C07 and stable model-aligned component_id values component_01_* through component_07_*. trading-evaluation owns orchestration and judgment, not duplicated trading decisions. Runtime decisions must keep crypto and equity/options in independent account sleeves without cross-account collateral, buying-power, position, or risk-budget netting.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_EXECRTC001';

UPDATE trading_registry
SET note = 'Task-level execution runtime component contract shared by live trading and Replay. Components expose component_step and component_name for concise intraday ordering, and component_id follows the stable model-aligned component_01_* through component_07_* naming pattern. Components call frozen model outputs as inputs, but execution owns trading lifecycle decisions.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'art_EXECRTC001';
