-- Register model-side evaluation artifact persistence entrypoint.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_MODEL_GOV_EVAL001',
    'script',
    'MODEL_EVALUATION_ARTIFACT_PERSISTENCE',
    'text',
    'PYTHONPATH=src python3 scripts/model_governance/persist_evaluation_artifacts.py',
    'trading-model/scripts/model_governance/persist_evaluation_artifacts.py',
    'trading-model;model_governance;model_dataset_snapshot;model_dataset_split;model_eval_label;model_eval_run;model_promotion_metric;no_model_activation;no_broker_execution',
    'sync_artifact',
    'Model-owned idempotent entrypoint for persisting evaluation artifact table rows into trading_model governance tables. It writes dataset/evaluation/metric evidence only and does not create manager decisions, activate configs, call providers, or mutate broker/account state.'
  ),
  (
    'trm_MODEL_GOV_EVAL001',
    'term',
    'MODEL_EVALUATION_ARTIFACT_TABLE_ROWS',
    'text',
    'model_evaluation_artifact_table_rows_v1',
    'trading-model/src/model_governance/evaluation/persistence.py',
    'trading-model;model_governance;evaluation_artifacts;promotion_evidence;sql_persistence',
    'sync_artifact',
    'JSON payload shape containing model_dataset_request, model_dataset_snapshot, model_dataset_split, model_eval_label, model_eval_run, and model_promotion_metric table rows for model-side governance persistence.'
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
