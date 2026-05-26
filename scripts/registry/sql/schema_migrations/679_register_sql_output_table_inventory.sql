-- Register accepted SQL output table inventory across data, model,
-- evaluation, and execution. These rows name stable schema.table contracts;
-- they do not create tables or authorize provider, broker, account, or
-- storage lifecycle mutation.

UPDATE trading_registry
SET payload = 'execution_realtime_data_interface',
    applies_to = replace(applies_to, 'execution_realtime_data_interface_v1', 'execution_realtime_data_interface'),
    note = 'Execution-side realtime market-data interface catalog. Realtime routes may share canonical providers with historical data, but use distinct realtime transports such as WebSocket streams or realtime HTTP snapshots.',
    updated_at = NOW()
WHERE key = 'EXECUTION_REALTIME_DATA_INTERFACE';

UPDATE trading_registry
SET payload = 'execution_broker_interface',
    applies_to = replace(applies_to, 'execution_broker_interface_v1', 'execution_broker_interface'),
    note = 'Execution broker/exchange interface catalog. OKX is accepted for crypto adapter scaffolding with live mutation disabled; Firstrade is recorded as deferred because no official trading API is accepted.',
    updated_at = NOW()
WHERE key = 'EXECUTION_BROKER_INTERFACE';

UPDATE trading_registry
SET payload = 'execution_capability_catalog',
    applies_to = replace(replace(applies_to, 'execution_realtime_data_interface_v1', 'execution_realtime_data_interface'), 'execution_broker_interface_v1', 'execution_broker_interface'),
    updated_at = NOW()
WHERE key = 'EXECUTION_CAPABILITY_CATALOG';

UPDATE trading_registry
SET applies_to = replace(replace(applies_to, 'execution_capability_catalog_v1', 'execution_capability_catalog'), 'execution_realtime_data_interface_v1', 'execution_realtime_data_interface'),
    updated_at = NOW()
WHERE key = 'EXECUTION_CAPABILITY_CATALOG_LIST';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_SQLINV001',
    'term',
    'M01_MARKET_REGIME_DATA_ACQUISITION_TABLE',
    'text',
    'trading_data.m01_market_regime_data_acquisition',
    'trading-data/docs/03_contracts.md;trading-manager/docs/28_numbering_physical_contract.md',
    'trading-data;m01_market_regime;data_acquisition;sql_table;canonical_sql_name',
    'registry_only',
    'Canonical schema-qualified SQL table name for M01 market-regime source/data-acquisition rows under the accepted owner-prefix/domain/task-stage naming rule.'
  ),
  (
    'trm_SQLINV002',
    'term',
    'M01_MARKET_REGIME_FEATURE_GENERATION_TABLE',
    'text',
    'trading_data.m01_market_regime_feature_generation',
    'trading-data/docs/03_contracts.md;trading-manager/docs/28_numbering_physical_contract.md',
    'trading-data;m01_market_regime;feature_generation;sql_table;canonical_sql_name',
    'registry_only',
    'Canonical schema-qualified SQL table name for deterministic M01 market-regime feature-generation rows.'
  ),
  (
    'trm_SQLINV003',
    'term',
    'M01_MARKET_REGIME_MODEL_GENERATION_TABLE',
    'text',
    'trading_model.m01_market_regime_model_generation',
    'trading-model/docs/03_contracts.md;trading-manager/docs/28_numbering_physical_contract.md',
    'trading-model;m01_market_regime;model_generation;sql_table;canonical_sql_name',
    'registry_only',
    'Canonical schema-qualified SQL table name for M01 MarketRegimeModel generation outputs.'
  ),
  (
    'trm_SQLINV004',
    'term',
    'M01_MARKET_REGIME_EXPLAINABILITY_TABLE',
    'text',
    'trading_model.m01_market_regime_explainability',
    'trading-model/docs/32_model_output_quality.md;trading-manager/docs/28_numbering_physical_contract.md',
    'trading-model;m01_market_regime;explainability;sql_table;canonical_sql_name',
    'registry_only',
    'Canonical schema-qualified SQL table name for M01 explainability support rows.'
  ),
  (
    'trm_SQLINV005',
    'term',
    'M01_MARKET_REGIME_DIAGNOSTICS_TABLE',
    'text',
    'trading_model.m01_market_regime_diagnostics',
    'trading-model/docs/32_model_output_quality.md;trading-manager/docs/28_numbering_physical_contract.md',
    'trading-model;m01_market_regime;diagnostics;sql_table;canonical_sql_name',
    'registry_only',
    'Canonical schema-qualified SQL table name for M01 diagnostics support rows.'
  ),
  (
    'trm_SQLINV006',
    'term',
    'M02_SECTOR_CONTEXT_DATA_ACQUISITION_TABLE',
    'text',
    'trading_data.m02_sector_context_data_acquisition',
    'trading-data/docs/03_contracts.md;trading-manager/docs/28_numbering_physical_contract.md',
    'trading-data;m02_sector_context;data_acquisition;sql_table;canonical_sql_name',
    'registry_only',
    'Canonical schema-qualified SQL table name for M02 sector-context data acquisition. Target-candidate pool generation is not the task-stage name.'
  ),
  (
    'trm_SQLINV007',
    'term',
    'M09_OPTION_EXPRESSION_CONTRACT_PATH_TABLE',
    'text',
    'trading_data.m09_option_expression_data_acquisition_contract_path',
    'trading-data/docs/03_contracts.md;trading-model/docs/03_contracts.md;trading-manager/docs/28_numbering_physical_contract.md',
    'trading-data;m09_option_expression;data_acquisition;contract_path;sql_table;canonical_sql_name',
    'registry_only',
    'Canonical schema-qualified SQL table name for M09 selected-option contract market-path tracking after contract selection. It is not order execution, position execution, or PnL labeling.'
  ),
  (
    'trm_SQLINV101',
    'term',
    'EVALUATION_REPLAY_CONTRACT_TABLE',
    'text',
    'trading_evaluation.replay_contract',
    'trading-evaluation/docs/20_replay_contracts.md',
    'trading-evaluation;replay_contract;sql_table;promotion_replay',
    'registry_only',
    'Canonical schema-qualified SQL table name for replay contract rows.'
  ),
  (
    'trm_SQLINV102',
    'term',
    'EVALUATION_REPLAY_DATASET_PREPARATION_TABLE',
    'text',
    'trading_evaluation.replay_dataset_preparation',
    'trading-evaluation/docs/22_replay_dataset_preparation.md',
    'trading-evaluation;replay_dataset_preparation;sql_table',
    'registry_only',
    'Canonical schema-qualified SQL table name for replay dataset preparation records.'
  ),
  (
    'trm_SQLINV103',
    'term',
    'EVALUATION_REPLAY_DATASET_FREEZE_TABLE',
    'text',
    'trading_evaluation.replay_dataset_freeze',
    'trading-evaluation/docs/22_replay_dataset_preparation.md',
    'trading-evaluation;replay_dataset_freeze;sql_table;frozen_snapshot',
    'registry_only',
    'Canonical schema-qualified SQL table name for replay dataset freeze records.'
  ),
  (
    'trm_SQLINV104',
    'term',
    'EVALUATION_REPLAY_SOURCE_COVERAGE_TABLE',
    'text',
    'trading_evaluation.replay_source_coverage',
    'trading-evaluation/docs/22_replay_dataset_preparation.md',
    'trading-evaluation;replay_source_coverage;sql_table',
    'registry_only',
    'Canonical schema-qualified SQL table name for replay source coverage rows.'
  ),
  (
    'trm_SQLINV105',
    'term',
    'EVALUATION_REPLAY_EXECUTION_RUN_TABLE',
    'text',
    'trading_evaluation.replay_execution_run',
    'trading-evaluation/docs/20_replay_contracts.md;trading-execution/docs/50_runtime_components.md',
    'trading-evaluation;replay_execution_run;trading-execution;sql_table',
    'registry_only',
    'Canonical schema-qualified SQL table name for replay execution-run records over the execution component graph.'
  ),
  (
    'trm_SQLINV106',
    'term',
    'EVALUATION_REPLAY_DECISION_TABLE',
    'text',
    'trading_evaluation.replay_decision',
    'trading-evaluation/docs/20_replay_contracts.md;trading-execution/docs/50_runtime_components.md',
    'trading-evaluation;replay_decision;runtime_component_graph;sql_table',
    'registry_only',
    'Canonical schema-qualified SQL table name for point-in-time Replay decision rows.'
  ),
  (
    'trm_SQLINV107',
    'term',
    'EVALUATION_REPLAY_PROGRESS_TABLE',
    'text',
    'trading_evaluation.replay_progress',
    'trading-evaluation/docs/20_replay_contracts.md',
    'trading-evaluation;replay_progress;sql_table',
    'registry_only',
    'Canonical schema-qualified SQL table name for Replay progress/status rows.'
  ),
  (
    'trm_SQLINV108',
    'term',
    'EVALUATION_FOLD_SETTLEMENT_RUN_TABLE',
    'text',
    'trading_evaluation.fold_settlement_run',
    'trading-evaluation/docs/30_fold_settlement.md',
    'trading-evaluation;fold_settlement_run;sql_table',
    'registry_only',
    'Canonical schema-qualified SQL table name for fold-settlement run records.'
  ),
  (
    'trm_SQLINV109',
    'term',
    'EVALUATION_FOLD_SETTLEMENT_METRIC_TABLE',
    'text',
    'trading_evaluation.fold_settlement_metric',
    'trading-evaluation/docs/30_fold_settlement.md',
    'trading-evaluation;fold_settlement_metric;sql_table',
    'registry_only',
    'Canonical schema-qualified SQL table name for fold-settlement metric rows.'
  ),
  (
    'trm_SQLINV110',
    'term',
    'EVALUATION_PROMOTION_ELIGIBILITY_DECISION_TABLE',
    'text',
    'trading_evaluation.promotion_eligibility_decision',
    'trading-evaluation/docs/50_promotion_readiness.md',
    'trading-evaluation;promotion_eligibility_decision;sql_table',
    'registry_only',
    'Canonical schema-qualified SQL table name for promotion eligibility decisions.'
  ),
  (
    'trm_SQLINV111',
    'term',
    'EVALUATION_PROMOTION_READINESS_RECORD_TABLE',
    'text',
    'trading_evaluation.promotion_readiness_record',
    'trading-evaluation/docs/50_promotion_readiness.md',
    'trading-evaluation;promotion_readiness_record;sql_table;execution_shadow_admission',
    'registry_only',
    'Canonical schema-qualified SQL table name for evaluation-owned promotion readiness records.'
  ),
  (
    'trm_SQLINV112',
    'term',
    'EVALUATION_PROMOTED_MODEL_PARAMETER_TABLE',
    'text',
    'trading_evaluation.promoted_model_parameter',
    'trading-evaluation/docs/50_promotion_readiness.md',
    'trading-evaluation;promoted_model_parameter;sql_table',
    'registry_only',
    'Canonical schema-qualified SQL table name for promoted-model parameter records.'
  ),
  (
    'trm_SQLINV201',
    'term',
    'EXECUTION_REALTIME_TRADING_RUNTIME_STATUS_TABLE',
    'text',
    'trading_execution.execution_realtime_trading_runtime_status',
    'trading-execution/docs/40_runtime_model_lifecycle.md',
    'trading-execution;realtime_trading_runtime;runtime_status;sql_table',
    'registry_only',
    'Canonical schema-qualified SQL table name for realtime trading runtime readiness/status records.'
  ),
  (
    'trm_SQLINV202',
    'term',
    'EXECUTION_CAPABILITY_CATALOG_TABLE',
    'text',
    'trading_execution.execution_capability_catalog',
    'trading-execution/docs/30_broker_interfaces.md',
    'trading-execution;execution_capability_catalog;sql_table;inspection',
    'registry_only',
    'Canonical schema-qualified SQL table name for side-effect-free execution capability catalog rows.'
  ),
  (
    'trm_SQLINV203',
    'term',
    'EXECUTION_REALTIME_DATA_INTERFACE_TABLE',
    'text',
    'trading_execution.execution_realtime_data_interface',
    'trading-execution/docs/03_contracts.md',
    'trading-execution;execution_realtime_data_interface;sql_table;realtime_market_data',
    'registry_only',
    'Canonical schema-qualified SQL table name for realtime data interface rows.'
  ),
  (
    'trm_SQLINV204',
    'term',
    'EXECUTION_BROKER_INTERFACE_TABLE',
    'text',
    'trading_execution.execution_broker_interface',
    'trading-execution/docs/30_broker_interfaces.md',
    'trading-execution;execution_broker_interface;sql_table;broker_interface',
    'registry_only',
    'Canonical schema-qualified SQL table name for broker/exchange interface rows.'
  ),
  (
    'trm_SQLINV205',
    'term',
    'EXECUTION_REALTIME_CAPTURE_CONTRACT_TABLE',
    'text',
    'trading_execution.realtime_capture_contract',
    'trading-execution/docs/03_contracts.md',
    'trading-execution;realtime_capture_contract;sql_table;input_snapshot',
    'registry_only',
    'Canonical schema-qualified SQL table name for realtime capture contract rows.'
  ),
  (
    'trm_SQLINV206',
    'term',
    'EXECUTION_REALTIME_FEATURE_SNAPSHOT_TABLE',
    'text',
    'trading_execution.realtime_feature_snapshot',
    'trading-execution/docs/03_contracts.md',
    'trading-execution;realtime_feature_snapshot;sql_table;input_snapshot',
    'registry_only',
    'Canonical schema-qualified SQL table name for realtime feature snapshots.'
  ),
  (
    'trm_SQLINV207',
    'term',
    'EXECUTION_MODEL_DECISION_INPUT_SNAPSHOT_TABLE',
    'text',
    'trading_execution.execution_model_decision_input_snapshot',
    'trading-execution/docs/03_contracts.md;trading-execution/docs/50_runtime_components.md',
    'trading-execution;execution_model_decision_input_snapshot;sql_table;model_input_handoff',
    'registry_only',
    'Canonical schema-qualified SQL table name for execution-owned model decision input snapshots.'
  ),
  (
    'trm_SQLINV208',
    'term',
    'EXECUTION_REALTIME_INPUT_COVERAGE_TABLE',
    'text',
    'trading_execution.execution_realtime_input_coverage',
    'trading-execution/docs/03_contracts.md',
    'trading-execution;execution_realtime_input_coverage;sql_table;coverage',
    'registry_only',
    'Canonical schema-qualified SQL table name for realtime input coverage rows.'
  ),
  (
    'trm_SQLINV209',
    'term',
    'EXECUTION_REALTIME_SUBSCRIPTION_PLAN_TABLE',
    'text',
    'trading_execution.execution_realtime_subscription_plan',
    'trading-execution/docs/03_contracts.md',
    'trading-execution;execution_realtime_subscription_plan;sql_table;subscription_plan',
    'registry_only',
    'Canonical schema-qualified SQL table name for realtime subscription plan rows.'
  ),
  (
    'trm_SQLINV210',
    'term',
    'EXECUTION_REALTIME_LIVE_OBSERVE_RESULT_TABLE',
    'text',
    'trading_execution.execution_realtime_live_observe_result',
    'trading-execution/docs/03_contracts.md',
    'trading-execution;execution_realtime_live_observe_result;sql_table;live_observe_result',
    'registry_only',
    'Canonical schema-qualified SQL table name for approved realtime observe results.'
  ),
  (
    'trm_SQLINV211',
    'term',
    'C01_INTAKE_SNAPSHOT_TABLE',
    'text',
    'trading_execution.c01_intake_snapshot',
    'trading-execution/docs/50_runtime_components.md',
    'component_01_intake;c01_intake_snapshot;sql_table;watch_targets',
    'registry_only',
    'Canonical schema-qualified SQL table name for C01 intake snapshots and watch-target routing evidence.'
  ),
  (
    'trm_SQLINV212',
    'term',
    'C02_ENTRY_DECISION_TABLE',
    'text',
    'trading_execution.c02_entry_decision',
    'trading-execution/docs/50_runtime_components.md',
    'component_02_entry;c02_entry_decision;sql_table;entry_thesis',
    'registry_only',
    'Canonical schema-qualified SQL table name for C02 underlying entry-thesis suitability decisions.'
  ),
  (
    'trm_SQLINV213',
    'term',
    'C03_POSITION_LIFECYCLE_DECISION_TABLE',
    'text',
    'trading_execution.c03_position_lifecycle_decision',
    'trading-execution/docs/50_runtime_components.md',
    'component_03_lifecycle;c03_position_lifecycle_decision;sql_table;existing_position_lifecycle',
    'registry_only',
    'Canonical schema-qualified SQL table name for C03 existing-position lifecycle decisions.'
  ),
  (
    'trm_SQLINV214',
    'term',
    'C04_OPTION_REEXPRESSION_DECISION_TABLE',
    'text',
    'trading_execution.c04_option_reexpression_decision',
    'trading-execution/docs/50_runtime_components.md',
    'component_04_option_review;c04_option_reexpression_decision;sql_table;option_expression',
    'registry_only',
    'Canonical schema-qualified SQL table name for C04 option expression/re-expression decisions.'
  ),
  (
    'trm_SQLINV215',
    'term',
    'C05_ORDER_INTENT_TABLE',
    'text',
    'trading_execution.c05_order_intent',
    'trading-execution/docs/50_runtime_components.md',
    'component_05_order_intent;c05_order_intent;sql_table;position_management',
    'registry_only',
    'Canonical schema-qualified SQL table name for C05 order-intent and position-management output.'
  ),
  (
    'trm_SQLINV216',
    'term',
    'C06_EXECUTION_GATE_RESULT_TABLE',
    'text',
    'trading_execution.c06_execution_gate_result',
    'trading-execution/docs/50_runtime_components.md',
    'component_06_execution_gate;c06_execution_gate_result;sql_table;agent_final_review',
    'registry_only',
    'Canonical schema-qualified SQL table name for C06 execution gate results.'
  ),
  (
    'trm_SQLINV217',
    'term',
    'C07_FAILURE_EXPLANATION_PACKET_TABLE',
    'text',
    'trading_execution.c07_failure_explanation_packet',
    'trading-execution/docs/50_runtime_components.md',
    'component_07_failure_review;c07_failure_explanation_packet;sql_table;post_failure_branch',
    'registry_only',
    'Canonical schema-qualified SQL table name for C07 post-failure explanation packets. It is not a normal pre-order gate.'
  ),
  (
    'trm_SQLINV218',
    'term',
    'C08_SHADOW_MODEL_RUNTIME_EVIDENCE_TABLE',
    'text',
    'trading_execution.c08_shadow_model_runtime_evidence',
    'trading-execution/docs/40_runtime_model_lifecycle.md',
    'component_08_shadow_model_runtime;c08_shadow_model_runtime_evidence;sql_table;market_hours_shadow',
    'registry_only',
    'Canonical schema-qualified SQL table name for C08 market-hours shadow runtime evidence.'
  ),
  (
    'trm_SQLINV219',
    'term',
    'C08_SHADOW_CYCLE_SELECTION_TABLE',
    'text',
    'trading_execution.c08_shadow_cycle_selection',
    'trading-execution/docs/40_runtime_model_lifecycle.md',
    'component_08_shadow_model_runtime;c08_shadow_cycle_selection;sql_table;active_model_selection',
    'registry_only',
    'Canonical schema-qualified SQL table name for C08 active/stable/probation/challenger roster selection.'
  ),
  (
    'trm_SQLINV220',
    'term',
    'C08_CAPACITY_SIMULATION_TABLE',
    'text',
    'trading_execution.c08_capacity_simulation',
    'trading-execution/docs/40_runtime_model_lifecycle.md',
    'component_08_shadow_model_runtime;c08_capacity_simulation;sql_table;capacity_gate',
    'registry_only',
    'Canonical schema-qualified SQL table name for C08 runtime capacity simulation rows.'
  ),
  (
    'trm_SQLINV221',
    'term',
    'EXECUTION_ACTIVE_MODEL_CONFIG_WRITE_TABLE',
    'text',
    'trading_execution.execution_active_model_config_write',
    'trading-execution/docs/40_runtime_model_lifecycle.md',
    'trading-execution;execution_active_model_config_write;sql_table;active_pointer_gate',
    'registry_only',
    'Canonical schema-qualified SQL table name for audited active-model config write records.'
  ),
  (
    'trm_SQLINV222',
    'term',
    'EXECUTION_ORDER_CONSTRUCTION_APPROVAL_TABLE',
    'text',
    'trading_execution.execution_order_construction_approval',
    'trading-execution/docs/30_broker_interfaces.md',
    'trading-execution;execution_order_construction_approval;sql_table;broker_order_construction',
    'registry_only',
    'Canonical schema-qualified SQL table name for broker-order construction approval evidence.'
  ),
  (
    'trm_SQLINV223',
    'term',
    'EXECUTION_BROKER_ORDER_INTENT_TABLE',
    'text',
    'trading_execution.execution_broker_order_intent',
    'trading-execution/docs/30_broker_interfaces.md',
    'trading-execution;execution_broker_order_intent;sql_table;broker_order_intent',
    'registry_only',
    'Canonical schema-qualified SQL table name for broker-shaped order intents before submission.'
  ),
  (
    'trm_SQLINV224',
    'term',
    'EXECUTION_BROKER_ORDER_INTENT_RESULT_TABLE',
    'text',
    'trading_execution.execution_broker_order_intent_result',
    'trading-execution/docs/30_broker_interfaces.md',
    'trading-execution;execution_broker_order_intent_result;sql_table;broker_order_intent',
    'registry_only',
    'Canonical schema-qualified SQL table name for broker-order-intent construction results.'
  ),
  (
    'trm_SQLINV225',
    'term',
    'TRADE_RISK_CAP_TABLE',
    'text',
    'trading_execution.trade_risk_cap',
    'trading-execution/docs/30_broker_interfaces.md;trading-execution/docs/50_runtime_components.md',
    'trading-execution;trade_risk_cap;sql_table;risk_gate',
    'registry_only',
    'Canonical schema-qualified SQL table name for trade risk-cap validation records.'
  ),
  (
    'trm_SQLINV226',
    'term',
    'REALTIME_MODEL_DECISION_EFFECTIVENESS_TABLE',
    'text',
    'trading_execution.realtime_model_decision_effectiveness',
    'trading-execution/docs/40_runtime_model_lifecycle.md',
    'trading-execution;realtime_model_decision_effectiveness;sql_table;runtime_attribution',
    'registry_only',
    'Canonical schema-qualified SQL table name for realtime model decision effectiveness summary records.'
  ),
  (
    'trm_SQLINV227',
    'term',
    'REALTIME_MODEL_DECISION_EFFECTIVENESS_ROW_TABLE',
    'text',
    'trading_execution.realtime_model_decision_effectiveness_row',
    'trading-execution/docs/40_runtime_model_lifecycle.md',
    'trading-execution;realtime_model_decision_effectiveness_row;sql_table;runtime_attribution',
    'registry_only',
    'Canonical schema-qualified SQL table name for realtime model decision effectiveness detail rows.'
  ),
  (
    'trm_SQLINV228',
    'term',
    'C07_FAILURE_ATTRIBUTION_TABLE',
    'text',
    'trading_execution.c07_failure_attribution',
    'trading-execution/docs/50_runtime_components.md',
    'component_07_failure_review;c07_failure_attribution;sql_table;post_failure_attribution',
    'registry_only',
    'Canonical schema-qualified SQL table name for C07 failure attribution rows.'
  ),
  (
    'trm_SQLINV229',
    'term',
    'RUNTIME_MODEL_LIFECYCLE_REVIEW_RESULT_TABLE',
    'text',
    'trading_execution.runtime_model_lifecycle_review_result',
    'trading-execution/docs/40_runtime_model_lifecycle.md',
    'trading-execution;runtime_model_lifecycle_review_result;sql_table;agent_review',
    'registry_only',
    'Canonical schema-qualified SQL table name for runtime-model lifecycle review results.'
  ),
  (
    'trm_SQLINV230',
    'term',
    'BROKER_ORDER_SUBMISSION_TABLE',
    'text',
    'trading_execution.broker_order_submission',
    'trading-execution/docs/30_broker_interfaces.md',
    'trading-execution;broker_order_submission;sql_table;future_gated_broker_mutation',
    'registry_only',
    'Reserved schema-qualified SQL table name for future gated broker order submission. It is outside the active current loop until explicit broker-submit acceptance.'
  ),
  (
    'trm_SQLINV231',
    'term',
    'BROKER_ORDER_STATE_TABLE',
    'text',
    'trading_execution.broker_order_state',
    'trading-execution/docs/30_broker_interfaces.md',
    'trading-execution;broker_order_state;sql_table;future_gated_broker_mutation',
    'registry_only',
    'Reserved schema-qualified SQL table name for future gated broker order-state evidence.'
  ),
  (
    'trm_SQLINV232',
    'term',
    'BROKER_FILL_TABLE',
    'text',
    'trading_execution.broker_fill',
    'trading-execution/docs/30_broker_interfaces.md',
    'trading-execution;broker_fill;sql_table;future_gated_broker_mutation',
    'registry_only',
    'Reserved schema-qualified SQL table name for future gated broker fill evidence.'
  ),
  (
    'trm_SQLINV233',
    'term',
    'ACCOUNT_STATE_SNAPSHOT_TABLE',
    'text',
    'trading_execution.account_state_snapshot',
    'trading-execution/docs/30_broker_interfaces.md',
    'trading-execution;account_state_snapshot;sql_table;future_gated_account_mutation',
    'registry_only',
    'Reserved schema-qualified SQL table name for future gated account-state snapshots.'
  ),
  (
    'trm_SQLINV234',
    'term',
    'POSITION_STATE_SNAPSHOT_TABLE',
    'text',
    'trading_execution.position_state_snapshot',
    'trading-execution/docs/30_broker_interfaces.md;trading-execution/docs/50_runtime_components.md',
    'trading-execution;position_state_snapshot;sql_table;future_gated_position_mutation',
    'registry_only',
    'Reserved schema-qualified SQL table name for future gated position-state snapshots.'
  ),
  (
    'trm_SQLINV235',
    'term',
    'EXECUTION_RECONCILIATION_RESULT_TABLE',
    'text',
    'trading_execution.execution_reconciliation_result',
    'trading-execution/docs/30_broker_interfaces.md',
    'trading-execution;execution_reconciliation_result;sql_table;future_gated_reconciliation',
    'registry_only',
    'Reserved schema-qualified SQL table name for future gated execution reconciliation results.'
  ),
  (
    'cfg_SQLINV001',
    'config',
    'SQL_OUTPUT_TABLE_INVENTORY_POLICY',
    'text',
    'schema_qualified_table_names_required;lowercase_snake_case;schema_dot_table_separator_only;no_hyphens;old_source_feature_model_prefixes_are_migration_debt;future_broker_account_tables_reserved_not_active',
    'trading-manager/docs/28_numbering_physical_contract.md;trading-manager/docs/03_contracts.md',
    'sql_table_inventory;canonical_sql_name;trading-data;trading-model;trading-evaluation;trading-execution',
    'registry_only',
    'Registry policy for SQL output table inventory: rows use schema-qualified lowercase snake_case table names. Future broker/account mutation table names may be reserved here, but registration does not authorize live broker submission, fills, reconciliation, account mutation, or position mutation.'
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
