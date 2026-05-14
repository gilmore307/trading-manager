-- Keep status_value rows limited to shared lifecycle/status domains.
-- selected_target_symbol_required is a workflow blocker token, not a reusable lifecycle status.

UPDATE trading_registry
SET kind = 'term',
    key = 'SELECTED_TARGET_SYMBOL_REQUIRED_BLOCKER',
    payload_format = 'text',
    applies_to = 'manager_model_training_workflow_plan;manager_model_training_workflow_state;manager_dataset_expansion_plan;layer_03_plus_blocker',
    note = 'Blocking workflow term used when Layer 3+ work is planned without a selected target symbol.',
    updated_at = NOW()
WHERE id = 'sts_DU001';
