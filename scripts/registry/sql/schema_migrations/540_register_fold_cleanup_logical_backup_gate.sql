-- Register fold-scoped cleanup gate and logical PostgreSQL backup plan.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_FOLDCLEAN001',
    'artifact_type',
    'MANAGER_FOLD_CLEANUP_PLAN',
    'text',
    'manager_fold_cleanup_plan',
    'trading-manager/src/trading_manager_tasks/fold_cleanup.py;trading-manager/scripts/tasks/plan_fold_cleanup.py;trading-manager/docs/26_historical_scheduler_runtime.md',
    'historical_scheduler;model_worker_1;fold_cleanup;storage_lifecycle;logical_backup;manager_model_training_workflow_state',
    'sync_artifact',
    'Manager-owned non-mutating fold cleanup gate. The cleanup granularity is fold_all_models_all_tasks_once: all model layers and all model-worker task types in the fold must complete before one fold-level backup and later storage lifecycle cleanup may proceed.'
  ),
  (
    'art_FOLDCLEAN002',
    'artifact_type',
    'MANAGER_FOLD_SQL_LOGICAL_BACKUP_PLAN',
    'text',
    'manager_fold_sql_logical_backup_plan',
    'trading-manager/src/trading_manager_tasks/fold_cleanup.py;trading-manager/docs/26_historical_scheduler_runtime.md',
    'historical_scheduler;model_worker_1;fold_cleanup;postgresql;logical_backup;pg_dump_custom',
    'sync_artifact',
    'Manager-owned backup precondition plan for fold cleanup. It requires one logical PostgreSQL pg_dump -Fc backup for the whole fold plus globals export, checksum, and restore smoke before cleanup; it does not perform database mutation.'
  ),
  (
    'cfg_FOLDCLEAN001',
    'config',
    'MANAGER_FOLD_CLEANUP_LOGICAL_BACKUP_POLICY',
    'text',
    'cleanup_after_all_models_all_tasks_complete;one_logical_backup_per_fold;pg_dump_custom;restore_smoke_required;no_model_by_model_cleanup',
    'trading-manager/docs/05_decision.md;trading-manager/docs/26_historical_scheduler_runtime.md;trading-manager/src/trading_manager_tasks/fold_cleanup.py',
    'historical_scheduler;model_worker_1;fold_cleanup;storage_lifecycle;postgresql;logical_backup',
    'sync_artifact',
    'Fold cleanup policy: cleanup is evaluated after the fold has all models and all tasks complete, one logical backup covers the whole fold, and cleanup is not per model. Manager plans the gate; storage owns lifecycle execution.'
  ),
  (
    'scr_FOLDCLEAN001',
    'script',
    'MANAGER_PLAN_FOLD_CLEANUP',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/plan_fold_cleanup.py --start-month ${START_MONTH} --end-month ${END_MONTH}',
    '/root/projects/trading-manager/scripts/tasks/plan_fold_cleanup.py;/root/projects/trading-manager/src/trading_manager_tasks/fold_cleanup.py',
    'manager_fold_cleanup_plan;manager_fold_sql_logical_backup_plan;historical_scheduler;model_worker_1;storage_lifecycle;plan_only',
    'sync_artifact',
    'Builds a non-mutating fold cleanup and SQL logical-backup plan. It reads model-worker fold state, requires all layers and task types complete, emits the pg_dump plan, and performs no provider calls, storage deletion, SQL mutation, model activation, broker execution, or account mutation.'
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
