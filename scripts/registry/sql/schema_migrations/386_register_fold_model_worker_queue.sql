-- Register the fold-scoped Model Worker queue/runtime boundary.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_MODWORK001',
    'config',
    'MODEL_WORKER_FOLD_QUEUE_RUNTIME',
    'text',
    'complete_six_month_foundation_fold_selects_model_worker_1',
    'trading-manager/src/trading_manager_tasks/scheduler_daemon.py;trading-manager/src/trading_manager_tasks/scheduler.py;trading-manager/docs/81_decision.md;trading-manager/docs/99_historical_scheduler_runtime.md',
    'historical_scheduler;model_worker_1;rolling_fold;promotion_review',
    'sync_artifact',
    'Model Worker 1 selects the earliest complete six-month Layer 1/2 foundation fold and runs fold-scoped model generation, model evaluation, Promotion Review, and maintenance while month-ingest lanes continue catch-up.'
  ),
  (
    'term_MODWORK001',
    'term',
    'MODEL_WORKER_FOLD_STATE',
    'text',
    'model_training_fold_state_<start>_<end>.json',
    'trading-manager/src/trading_manager_tasks/scheduler_daemon.py;trading-manager/src/trading_manager_tasks/dashboard_read_models.py',
    'model_worker_1;workflow_state;dashboard_task_timeline',
    'sync_artifact',
    'Fold-scoped workflow checkpoint seeded from complete month-scoped Layer 1/2 substrate states; it must not overwrite month-ingest checkpoints.'
  ),
  (
    'term_MODWORK002',
    'term',
    'ROLLING_FOLD_4_1_1_READY_RULE',
    'text',
    'train_2016-01_2016-04_validation_2016-05_test_2016-06_requires_all_six_months_foundation_ready',
    'trading-manager/src/trading_manager_tasks/scheduler_daemon.py;trading-manager/docs/81_decision.md',
    'rolling_fold;dataset_split;model_evaluation;promotion_review',
    'sync_artifact',
    'A 4+1+1 fold becomes eligible only after all six month-scoped Layer 1/2 substrate states are complete; the first fold is 2016-01 through 2016-06.'
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
