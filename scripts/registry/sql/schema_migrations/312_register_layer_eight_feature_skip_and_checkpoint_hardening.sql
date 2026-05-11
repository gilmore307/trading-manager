-- Register Layer 8 no-provider feature-skip automation and checkpoint/approval hardening.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_L8FEAT001',
    'script',
    'LAYER_08_OPTION_EXPRESSION_FEATURE_GENERATION',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/execute_layer_eight_option_feature_generation.py --start-month ${START_MONTH} --end-month ${END_MONTH}',
    '/root/projects/trading-manager/scripts/tasks/execute_layer_eight_option_feature_generation.py',
    'layer_08_option_expression;feature_08_option_expression;source_05_option_expression;safe_offline_model_training',
    'sync_artifact',
    'Manager-owned Layer 8 feature-stage adapter. It writes a first-class no-provider/no-feature skip receipt when the reviewed gate has zero active target chains, or delegates to trading-data feature_08 option-expression generation after approved active-path acquisition.'
  ),
  (
    'term_L8FEATSKIP001',
    'term',
    'LAYER_08_OPTION_EXPRESSION_FEATURE_NO_PROVIDER_SKIP_RECEIPT',
    'text',
    'layer_08_option_expression_feature_generation_no_provider_skip_receipt_v1',
    'trading-manager/docs/95_task_system.md',
    'layer_08_option_expression;feature_08_option_expression;manager_model_training_workflow_state_v1',
    'sync_artifact',
    'Component completion receipt proving Layer 8 feature generation is a reviewed no-op when the Layer 8 gate accepted no active target chain and therefore no source_05/feature_08 rows are required before deterministic no-option model generation.'
  ),
  (
    'term_MWFSTATE002',
    'term',
    'MANAGER_MODEL_TRAINING_MONTH_SCOPED_CHECKPOINT',
    'text',
    'storage/runtime/model_training_workflow_state_YYYY-MM.json',
    'trading-manager/docs/80_task.md',
    'manager_model_training_workflow_state_v1;historical_backfill;automation_scheduler',
    'sync_artifact',
    'Default scheduler-owned month-scoped checkpoint path for the Layer 1-8 historical-training workflow, preventing chronological months from sharing a mutable global workflow state file.'
  ),
  (
    'term_MWFSTATE003',
    'term',
    'MANAGER_WORKFLOW_PROVIDER_CALLS_OBSERVED',
    'text',
    'provider_calls_observed',
    'trading-manager/docs/95_task_system.md',
    'manager_model_training_workflow_state_v1;live_call_approval_v1;provider_dispatch',
    'sync_artifact',
    'Workflow-state counter for approved provider calls observed from ingested receipts, kept separate from safe/offline stage provider_calls so dashboards do not hide acquisition calls or misclassify offline stages.'
  ),
  (
    'term_LCAPKT004',
    'term',
    'LIVE_CALL_APPROVAL_PACKET_REVIEWED_APPROVAL_ARTIFACT',
    'text',
    'reviewed_approval.json',
    'trading-manager/docs/95_task_system.md',
    'manager_live_call_approval_packet_v1;live_call_approval_v1;manager_live_call_approval_proposal_validation_v1',
    'sync_artifact',
    'Editable working approval artifact inside a live-call approval packet. The template remains reviewed_approval_TEMPLATE.json; operators review/edit reviewed_approval.json before proposal-bound validation.'
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
