-- Register corrected boundary: substrate stages are month-scoped; model/promotion stages are fold-scoped.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
    'cfg_FOLDSTAGE001',
    'config',
    'MONTHLY_SUBSTRATE_FOLD_MODEL_STAGE_BOUNDARY',
    'text',
    'data_acquisition_and_feature_generation_are_month_scoped;model_generation_and_later_are_fold_scoped',
    'trading-manager/src/trading_manager_tasks/model_training_workflow.py;trading-manager/src/trading_manager_tasks/scheduler_daemon.py;trading-manager/docs/99_historical_scheduler_runtime.md',
    'historical_scheduler;month_ingest_workers;model_worker_1;data_acquisition;feature_generation;model_generation;model_evaluation;promotion_review;maintenance',
    'sync_artifact',
    'Month Ingest Workers own single-month substrate stages: data_acquisition and feature_generation/input preparation. Model Worker 1 owns only fold-scoped model_generation, model_evaluation, promotion_review, and maintenance after every month in the fold has completed substrate stages.'
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
