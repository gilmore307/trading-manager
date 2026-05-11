-- Register the no-provider Layer 8 option-expression gate review.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_L8GATE001',
    'script',
    'LAYER_08_OPTION_EXPRESSION_GATE_REVIEW',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/review_layer_eight_option_expression_gate.py --start-month ${START_MONTH} --end-month ${END_MONTH} --write',
    '/root/projects/trading-manager/scripts/tasks/review_layer_eight_option_expression_gate.py',
    'layer_08_option_expression;option_expression_model;source_05_option_expression;live_call_approval_v1;safe_offline_model_training',
    'sync_artifact',
    'Manager-owned no-provider review before Layer 8 option-expression acquisition. It reads completed Layer 7 underlying-action rows, previews ThetaData/source_05 option-snapshot requests only for active target chains, or records a reviewed no-active-target skip when all Layer 7 rows are no-trade/maintain/neutral.'
  ),
  (
    'term_L8GATE001',
    'term',
    'MANAGER_LAYER_08_OPTION_EXPRESSION_GATE_REVIEW',
    'text',
    'manager_layer_08_option_expression_gate_review_v1',
    'trading-manager/docs/95_task_system.md',
    'layer_08_option_expression;option_expression_model;source_05_option_expression;live_call_approval_v1;manager_stage_coverage_v1',
    'sync_artifact',
    'Layer 8 gate-review artifact that separates approval-needed active option-expression target chains from reviewed no-provider skips. The artifact is plan/review evidence only and performs no provider calls, broker execution, model activation, or storage lifecycle mutation.'
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
