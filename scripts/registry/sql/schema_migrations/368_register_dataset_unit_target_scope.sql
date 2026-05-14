-- Register explicit historical-training dataset unit and target-scope policy.
-- Layers 1-2 use six-month panel units; Layers 3-8 require a target symbol plus six-month unit.

UPDATE trading_registry
SET payload = 'layer_01_background_panel_six_month_unit;layer_02_sector_panel_six_month_unit;layers_03_07_target_symbol_six_month_unit;layer_08_option_expression_after_target_chain_complete;selected_target_symbol_required_for_layer_03_plus;reviewed_exception_required_for_target_fanout',
    note = 'Formal workflow progression is segmented by dataset unit: Layers 1-2 are finite six-month panel flows with no single target symbol; Layers 3-7 run target-major one selected target symbol over one six-month unit before the next target by default; Layer 8 option-expression expansion waits for the completed upstream target chain. Layer 3+ task plans must expose selected_target_symbol and block with selected_target_symbol_required when omitted.',
    updated_at = NOW()
WHERE id = 'cfg_MWFP002';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'term_DU001',
    'term',
    'HISTORICAL_DATASET_UNIT_POLICY',
    'text',
    'layers_01_02_six_month_panel;layers_03_08_target_symbol_six_month',
    'trading-manager/docs/98_automation_scheduler.md;trading-manager/docs/99_historical_scheduler_runtime.md;trading-manager/docs/100_dataset_expansion.md',
    'historical_scheduler;model_training_workflow;dataset_expansion;manager_model_training_workflow_plan;manager_model_training_workflow_state',
    'sync_artifact',
    'Accepted dataset-unit policy: Layers 1-2 use one six-month panel as the work unit; Layers 3-8 use one selected target symbol over one six-month window, with Layer 8 expanding option-expression buckets only after the selected target chain is complete.'
  ),
  (
    'cfg_DU001',
    'config',
    'TRADING_MANAGER_DATASET_UNIT_MONTHS',
    'text',
    '6',
    'trading-manager/docs/98_automation_scheduler.md;trading-manager/docs/99_historical_scheduler_runtime.md;trading-manager/docs/100_dataset_expansion.md',
    'historical_scheduler;model_training_workflow;dataset_expansion;dataset_unit',
    'sync_artifact',
    'Accepted historical-training dataset unit length in months for the current manager workflow policy.'
  ),
  (
    'cfg_DU002',
    'config',
    'TRADING_MANAGER_INITIAL_SELECTED_TARGET_SYMBOL',
    'text',
    'SPY',
    'trading-manager/deploy/systemd/trading-manager-historical-scheduler.env;trading-manager/deploy/systemd/trading-manager-historical-scheduler.service;trading-manager/docs/99_historical_scheduler_runtime.md',
    'historical_scheduler;model_training_workflow;selected_target_symbol;layer_03_plus',
    'sync_artifact',
    'Reviewed initial target symbol for the first Layer 3+ six-month dataset unit in the service template. Operators may override it for later target expansion.'
  ),
  (
    'fld_DU001',
    'field',
    'DATASET_UNIT_KIND',
    'field_name',
    'dataset_unit_kind',
    'trading-manager/src/trading_manager_tasks/model_training_workflow.py;trading-manager/src/trading_manager_tasks/dataset_expansion.py;trading-manager/docs/100_dataset_expansion.md',
    'manager_model_training_workflow_plan;manager_model_training_workflow_state;manager_dataset_expansion_plan;dashboard_task_timeline',
    'sync_artifact',
    'Manager-visible field naming whether the work unit is a six-month panel or target-symbol six-month unit.'
  ),
  (
    'fld_DU002',
    'field',
    'DATASET_UNIT_MONTHS',
    'field_name',
    'dataset_unit_months',
    'trading-manager/src/trading_manager_tasks/model_training_workflow.py;trading-manager/src/trading_manager_tasks/dataset_expansion.py;trading-manager/docs/100_dataset_expansion.md',
    'manager_model_training_workflow_plan;manager_model_training_workflow_state;manager_dataset_expansion_plan;dashboard_task_timeline',
    'sync_artifact',
    'Manager-visible field for the number of months in the dataset unit; currently six.'
  ),
  (
    'fld_DU003',
    'field',
    'SELECTED_TARGET_SYMBOL',
    'field_name',
    'selected_target_symbol',
    'trading-manager/src/trading_manager_tasks/model_training_workflow.py;trading-manager/docs/99_historical_scheduler_runtime.md;trading-manager/docs/100_dataset_expansion.md',
    'manager_model_training_workflow_plan;manager_dataset_expansion_plan;historical_scheduler;layer_03_plus',
    'sync_artifact',
    'Task-scope target symbol selected for Layer 3+ target-symbol six-month dataset units.'
  ),
  (
    'fld_DU004',
    'field',
    'TARGET_SYMBOL',
    'field_name',
    'target_symbol',
    'trading-manager/src/trading_manager_tasks/model_training_workflow.py;trading-manager/src/trading_manager_tasks/dataset_expansion.py;trading-manager/src/trading_manager_tasks/dashboard_read_models.py',
    'manager_model_training_workflow_plan;manager_model_training_workflow_state;manager_dataset_expansion_plan;dashboard_task_timeline;layer_03_plus',
    'sync_artifact',
    'Per-stage or per-decision target symbol for target-major Layer 3+ dataset work. It is null for Layer 1-2 panel units.'
  ),
  (
    'sts_DU001',
    'status_value',
    'SELECTED_TARGET_SYMBOL_REQUIRED',
    'status_value',
    'selected_target_symbol_required',
    'trading-manager/src/trading_manager_tasks/model_training_workflow.py;trading-manager/docs/99_historical_scheduler_runtime.md;trading-manager/docs/100_dataset_expansion.md',
    'manager_model_training_workflow_plan;manager_model_training_workflow_state;manager_dataset_expansion_plan;layer_03_plus_blocker',
    'sync_artifact',
    'Blocking status/blocker value used when Layer 3+ work is planned without a selected target symbol.'
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
