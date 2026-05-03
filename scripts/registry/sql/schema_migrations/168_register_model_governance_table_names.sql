INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_MDGOV001',
    'term',
    'MODEL_DATASET_REQUEST_TABLE',
    'text',
    'model_dataset_request',
    'trading-model/docs/05_decision.md',
    'trading-model;trading-manager;model_governance;model_data_request',
    'registry_only',
    'Accepted generic trading_model governance table name for model-originated data coverage requests. The table records required source/derived data windows such as required_data_start_time and required_data_end_time; model-local label horizons and split rules are intentionally outside the manager-facing request contract.'
  ),
  (
    'trm_MDGOV002',
    'term',
    'MODEL_DATASET_SNAPSHOT_TABLE',
    'text',
    'model_dataset_snapshot',
    'trading-model/docs/05_decision.md',
    'trading-model;model_governance;model_dataset_snapshot',
    'registry_only',
    'Accepted generic trading_model governance table name for freezing the data/config version used by an evaluation or model comparison. Concrete columns are intentionally not registered yet.'
  ),
  (
    'trm_MDGOV003',
    'term',
    'MODEL_DATASET_SPLIT_TABLE',
    'text',
    'model_dataset_split',
    'trading-model/docs/05_decision.md',
    'trading-model;model_governance;model_dataset_split',
    'registry_only',
    'Accepted generic trading_model governance table name for train/validation/test/holdout split windows attached to a dataset snapshot. Concrete columns are intentionally not registered yet.'
  ),
  (
    'trm_MDGOV004',
    'term',
    'MODEL_EVAL_LABEL_TABLE',
    'text',
    'model_eval_label',
    'trading-model/docs/05_decision.md',
    'trading-model;model_governance;model_evaluation',
    'registry_only',
    'Accepted generic trading_model governance table name for model-owned evaluation labels. Label horizons, targets, and label construction rules are model semantics, not manager-facing data request fields. Concrete columns are intentionally not registered yet.'
  ),
  (
    'trm_MDGOV005',
    'term',
    'MODEL_EVAL_RUN_TABLE',
    'text',
    'model_eval_run',
    'trading-model/docs/05_decision.md',
    'trading-model;model_governance;model_evaluation',
    'registry_only',
    'Accepted generic trading_model governance table name for evaluation run metadata across model layers. Concrete columns are intentionally not registered yet.'
  ),
  (
    'trm_MDGOV006',
    'term',
    'MODEL_EVAL_METRIC_TABLE',
    'text',
    'model_eval_metric',
    'trading-model/docs/05_decision.md',
    'trading-model;model_governance;model_evaluation',
    'registry_only',
    'Accepted generic trading_model governance table name for evaluation metrics across model layers, factors, targets, horizons, and dataset splits. Concrete columns are intentionally not registered yet.'
  )
ON CONFLICT (id) DO UPDATE SET
    kind = excluded.kind,
    key = excluded.key,
    payload_format = excluded.payload_format,
    payload = excluded.payload,
    path = excluded.path,
    applies_to = excluded.applies_to,
    artifact_sync_policy = excluded.artifact_sync_policy,
    note = excluded.note,
    updated_at = CURRENT_TIMESTAMP;
