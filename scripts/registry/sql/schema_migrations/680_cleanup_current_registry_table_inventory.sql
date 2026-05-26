-- Clean the active registry table inventory after the first full pass.
-- This migration keeps append-only history intact while removing stale
-- current rows, aligning execution SQL table names to the current
-- status/realtime/trade/performance families, and replacing the old
-- source_NN/feature_NN/model_NN SQL naming policy.

UPDATE trading_registry
SET payload = 'use_mNN_domain_task_stage_sql_names;old_source_feature_model_prefixes_are_migration_debt;layer_neutral_tables_do_not_invent_layer_numbers;layer_refs_live_in_fields_for_neutral_tables',
    path = 'scripts/registry/rules/model-layer-naming.md;scripts/registry/rules/sql-table-surface-naming.md',
    applies_to = 'trading_data;trading_model;trading_evaluation;trading_execution;sql_table_naming;model_layer_naming;dashboard_data_tables',
    note = 'Current SQL table naming policy: model/data SQL tables use schema-qualified mNN_domain_task_stage names such as trading_data.m01_market_regime_data_acquisition and trading_model.m01_market_regime_model_generation. Old source_NN, feature_NN, and model_NN surface stems are migration debt, not current planning names. Layer-neutral governance, control-plane, registry, receipt, and audit tables must not invent fake layer prefixes; they carry layer refs in row fields when needed.',
    updated_at = NOW()
WHERE key = 'SQL_LAYER_TABLE_NAMING_POLICY';

WITH updates(id, key, payload, applies_to, note) AS (
  VALUES
    (
      'trm_SQLINV004',
      'M01_MARKET_REGIME_MODEL_GENERATION_EXPLAINABILITY_TABLE',
      'trading_model.m01_market_regime_model_generation_explainability',
      'trading-model;m01_market_regime;model_generation;explainability;sql_table;canonical_sql_name',
      'Canonical schema-qualified SQL table name for M01 model-generation explainability support rows.'
    ),
    (
      'trm_SQLINV005',
      'M01_MARKET_REGIME_MODEL_GENERATION_DIAGNOSTICS_TABLE',
      'trading_model.m01_market_regime_model_generation_diagnostics',
      'trading-model;m01_market_regime;model_generation;diagnostics;sql_table;canonical_sql_name',
      'Canonical schema-qualified SQL table name for M01 model-generation diagnostics support rows.'
    ),
    (
      'trm_SQLINV201',
      'STATUS_REALTIME_TRADING_RUNTIME_TABLE',
      'trading_execution.status_realtime_trading_runtime',
      'trading-execution;status_realtime_trading_runtime;runtime_status;sql_table',
      'Canonical schema-qualified SQL table name for realtime trading runtime readiness/status records.'
    ),
    (
      'trm_SQLINV202',
      'STATUS_CAPABILITY_CATALOG_TABLE',
      'trading_execution.status_capability_catalog',
      'trading-execution;status_capability_catalog;sql_table;inspection',
      'Canonical schema-qualified SQL table name for side-effect-free execution capability catalog rows.'
    ),
    (
      'trm_SQLINV203',
      'STATUS_REALTIME_DATA_INTERFACE_TABLE',
      'trading_execution.status_realtime_data_interface',
      'trading-execution;status_realtime_data_interface;sql_table;realtime_market_data',
      'Canonical schema-qualified SQL table name for realtime data interface status rows.'
    ),
    (
      'trm_SQLINV204',
      'STATUS_BROKER_INTERFACE_TABLE',
      'trading_execution.status_broker_interface',
      'trading-execution;status_broker_interface;sql_table;broker_interface',
      'Canonical schema-qualified SQL table name for broker/exchange interface posture rows.'
    ),
    (
      'trm_SQLINV205',
      'REALTIME_CAPTURE_CONTRACT_TABLE',
      'trading_execution.realtime_capture_contract',
      'trading-execution;realtime_capture_contract;sql_table;input_snapshot',
      'Canonical schema-qualified SQL table name for realtime capture contract rows.'
    ),
    (
      'trm_SQLINV206',
      'REALTIME_FEATURE_SNAPSHOT_TABLE',
      'trading_execution.realtime_feature_snapshot',
      'trading-execution;realtime_feature_snapshot;sql_table;input_snapshot',
      'Canonical schema-qualified SQL table name for realtime feature snapshots.'
    ),
    (
      'trm_SQLINV207',
      'REALTIME_MODEL_DECISION_INPUT_SNAPSHOT_TABLE',
      'trading_execution.realtime_model_decision_input_snapshot',
      'trading-execution;realtime_model_decision_input_snapshot;sql_table;model_input_handoff',
      'Canonical schema-qualified SQL table name for realtime model-decision input snapshots.'
    ),
    (
      'trm_SQLINV208',
      'REALTIME_INPUT_COVERAGE_TABLE',
      'trading_execution.realtime_input_coverage',
      'trading-execution;realtime_input_coverage;sql_table;coverage',
      'Canonical schema-qualified SQL table name for realtime input coverage rows.'
    ),
    (
      'trm_SQLINV209',
      'REALTIME_SUBSCRIPTION_PLAN_TABLE',
      'trading_execution.realtime_subscription_plan',
      'trading-execution;realtime_subscription_plan;sql_table;subscription_plan',
      'Canonical schema-qualified SQL table name for realtime subscription plan rows.'
    ),
    (
      'trm_SQLINV210',
      'REALTIME_LIVE_OBSERVE_RESULT_TABLE',
      'trading_execution.realtime_live_observe_result',
      'trading-execution;realtime_live_observe_result;sql_table;live_observe_result',
      'Canonical schema-qualified SQL table name for approved realtime observe results.'
    ),
    (
      'trm_SQLINV218',
      'PERFORMANCE_MODEL_RUNTIME_EVIDENCE_TABLE',
      'trading_execution.performance_model_runtime_evidence',
      'trading-execution;performance_model_runtime_evidence;sql_table;market_hours_shadow',
      'Canonical schema-qualified SQL table name for market-hours promoted-model runtime evidence. Raw C08 runtime evidence belongs to performance rows; C08 component output remains c08_shadow_cycle_selection.'
    ),
    (
      'trm_SQLINV220',
      'PERFORMANCE_RUNTIME_CAPACITY_SIMULATION_TABLE',
      'trading_execution.performance_runtime_capacity_simulation',
      'trading-execution;performance_runtime_capacity_simulation;sql_table;capacity_gate',
      'Reserved schema-qualified SQL table name for reviewed runtime capacity simulation evidence. It is not the C08 component-owned cycle-selection output.'
    ),
    (
      'trm_SQLINV221',
      'STATUS_ACTIVE_MODEL_CONFIG_WRITE_TABLE',
      'trading_execution.status_active_model_config_write',
      'trading-execution;status_active_model_config_write;sql_table;active_pointer_gate',
      'Canonical schema-qualified SQL table name for audited active-model config write records.'
    ),
    (
      'trm_SQLINV222',
      'TRADE_ORDER_CONSTRUCTION_APPROVAL_TABLE',
      'trading_execution.trade_order_construction_approval',
      'trading-execution;trade_order_construction_approval;sql_table;broker_order_construction',
      'Canonical schema-qualified SQL table name for broker-order construction approval evidence.'
    ),
    (
      'trm_SQLINV223',
      'TRADE_BROKER_ORDER_INTENT_TABLE',
      'trading_execution.trade_broker_order_intent',
      'trading-execution;trade_broker_order_intent;sql_table;broker_order_intent',
      'Canonical schema-qualified SQL table name for broker-shaped order intents before submission.'
    ),
    (
      'trm_SQLINV224',
      'TRADE_BROKER_ORDER_INTENT_RESULT_TABLE',
      'trading_execution.trade_broker_order_intent_result',
      'trading-execution;trade_broker_order_intent_result;sql_table;broker_order_intent',
      'Canonical schema-qualified SQL table name for broker-order-intent construction results.'
    ),
    (
      'trm_SQLINV226',
      'PERFORMANCE_MODEL_DECISION_EFFECTIVENESS_TABLE',
      'trading_execution.performance_model_decision_effectiveness',
      'trading-execution;performance_model_decision_effectiveness;sql_table;runtime_attribution',
      'Canonical schema-qualified SQL table name for realtime/shadow model decision effectiveness summary records.'
    ),
    (
      'trm_SQLINV227',
      'PERFORMANCE_MODEL_DECISION_EFFECTIVENESS_ROW_TABLE',
      'trading_execution.performance_model_decision_effectiveness_row',
      'trading-execution;performance_model_decision_effectiveness_row;sql_table;runtime_attribution',
      'Canonical schema-qualified SQL table name for realtime/shadow model decision effectiveness detail rows.'
    ),
    (
      'trm_SQLINV229',
      'PERFORMANCE_RUNTIME_MODEL_LIFECYCLE_REVIEW_TABLE',
      'trading_execution.performance_runtime_model_lifecycle_review',
      'trading-execution;performance_runtime_model_lifecycle_review;sql_table;agent_review',
      'Canonical schema-qualified SQL table name for runtime-model lifecycle review results.'
    ),
    (
      'trm_SQLINV230',
      'TRADE_BROKER_ORDER_SUBMISSION_TABLE',
      'trading_execution.trade_broker_order_submission',
      'trading-execution;trade_broker_order_submission;sql_table;future_gated_broker_mutation',
      'Reserved schema-qualified SQL table name for future gated broker order submission. It is outside the active current loop until explicit broker-submit acceptance.'
    ),
    (
      'trm_SQLINV231',
      'TRADE_BROKER_ORDER_STATE_TABLE',
      'trading_execution.trade_broker_order_state',
      'trading-execution;trade_broker_order_state;sql_table;future_gated_broker_mutation',
      'Reserved schema-qualified SQL table name for future gated broker order-state evidence.'
    ),
    (
      'trm_SQLINV232',
      'TRADE_BROKER_FILL_TABLE',
      'trading_execution.trade_broker_fill',
      'trading-execution;trade_broker_fill;sql_table;future_gated_broker_mutation',
      'Reserved schema-qualified SQL table name for future gated broker fill evidence.'
    ),
    (
      'trm_SQLINV233',
      'TRADE_ACCOUNT_STATE_SNAPSHOT_TABLE',
      'trading_execution.trade_account_state_snapshot',
      'trading-execution;trade_account_state_snapshot;sql_table;future_gated_account_mutation',
      'Reserved schema-qualified SQL table name for future gated account-state snapshots.'
    ),
    (
      'trm_SQLINV234',
      'TRADE_POSITION_STATE_SNAPSHOT_TABLE',
      'trading_execution.trade_position_state_snapshot',
      'trading-execution;trade_position_state_snapshot;sql_table;future_gated_position_mutation',
      'Reserved schema-qualified SQL table name for future gated position-state snapshots.'
    ),
    (
      'trm_SQLINV235',
      'TRADE_RECONCILIATION_RESULT_TABLE',
      'trading_execution.trade_reconciliation_result',
      'trading-execution;trade_reconciliation_result;sql_table;future_gated_reconciliation',
      'Reserved schema-qualified SQL table name for future gated execution reconciliation results.'
    )
)
UPDATE trading_registry
SET key = updates.key,
    payload = updates.payload,
    applies_to = updates.applies_to,
    note = updates.note,
    updated_at = NOW()
FROM updates
WHERE trading_registry.id = updates.id;

UPDATE trading_registry
SET payload = replace(payload, 'single_leg_long_call_put_v1', 'single_leg_long_call_put'),
    note = replace(replace(replace(replace(replace(note, 'Layer 9 V1', 'Layer 9 current'), ' V1 ', ' current '), 'V1 supports', 'Current scope supports'), 'beyond V1', 'beyond current scope'), 'V1 avoids', 'Current policy avoids'),
    updated_at = NOW()
WHERE key IN (
  'C04_OPTION_EXPRESSION_REVIEW_POLICY',
  'LAYER_09_OPTION_EXPRESSION_SINGLE_LEG_POLICY',
  'OPTION_EXPRESSION_DELTA_POLICY',
  'OPTION_EXPRESSION_DTE_POLICY',
  'OPTION_EXPRESSION_MONEYNESS_GUARDRAIL',
  'OPTION_EXPRESSION_TYPES'
);

DELETE FROM trading_registry
WHERE key IN (
  'ACTIVATION_RECORD_ARTIFACT',
  'DATA_SOURCES_GLOBAL_CONFIG_DEPRECATED',
  'EXECUTION_REALTIME_RUNTIME_CHECK_TIMER',
  'EARNINGS_GUIDANCE_ARTIFACT_COVERAGE_SCOUT_Q4_2025',
  'EARNINGS_GUIDANCE_ARTIFACT_COVERAGE_WITH_DOCUMENTS_Q4_2025'
);
