-- Register manager-owned model-worker target rotation contracts.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_MGRTRGROT001',
    'artifact_type',
    'MANAGER_MODEL_WORKER_TARGET_SELECTION',
    'text',
    'manager_model_worker_target_selection',
    'trading-manager/src/trading_manager_tasks/scheduler_daemon.py;trading-manager/docs/25_automation_scheduler.md',
    'trading-manager;historical_scheduler;model_worker;target_rotation;layer_03_plus_training',
    'sync_artifact',
    'Manager scheduler selection artifact for Layer 3+ target-scoped model-worker training. It records the selected target, target queue, reason code, and fold selection. It is execution routing evidence only and is not promotion evidence.'
  ),
  (
    'art_MGRTRGROT002',
    'artifact_type',
    'MANAGER_MODEL_TRAINING_TARGET_QUEUE',
    'text',
    'manager_model_training_target_queue',
    'trading-manager/docs/25_automation_scheduler.md',
    'trading-manager;historical_scheduler;model_worker;target_queue;layer_03_plus_training',
    'sync_artifact',
    'Ordered runtime JSON queue for target-scoped Layer 3+ model-worker training. When no target is pinned, manager selects the first queued target with an open or unstarted eligible fold.'
  ),
  (
    'term_MGRTRGROT001',
    'term',
    'TARGET_SCOPED_MODEL_WORKER_FOLD_STATE',
    'text',
    'model_training_fold_state_<target>_<start_month>_<end_month>.json',
    'trading-manager/src/trading_manager_tasks/scheduler_daemon.py;trading-manager/docs/05_decision.md',
    'trading-manager;historical_scheduler;model_worker;fold_state;target_rotation',
    'sync_artifact',
    'Target-scoped model-worker fold checkpoint naming pattern. Separate target tokens prevent one caught-up target from consuming or overwriting another target training chain that restarts at 2016-01.'
  ),
  (
    'term_STORLIFEAGENT001',
    'term',
    'AGENT_STORAGE_LIFECYCLE_DECISION',
    'text',
    'agent_storage_lifecycle_decision',
    'trading-manager/docs/05_decision.md;trading-storage/docs/20_storage_lifecycle_policy.md',
    'trading-manager;trading-storage;storage_lifecycle;agent_storage_lifecycle_decision;storage-lifecycle-review',
    'sync_artifact',
    'Storage lifecycle policy/agent decision evidence for storage lifecycle mutation. Reviewer agents must use the storage-lifecycle-review skill; accepted deletion is deletion, not relocation to a trash-preservation folder.'
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

UPDATE trading_registry
SET note = 'Runs the persistent historical-training automation scheduler daemon. It can auto-select month-ingest work, run target-scoped model-worker folds, and rotate Layer 3+ training targets from the runtime target queue after the current target is caught up through the completed-month cutoff.',
    applies_to = 'trading-manager;historical_scheduler;model_worker;target_rotation;month_ingest_worker_lanes;dashboard_refresh',
    updated_at = now()
WHERE key = 'RUN_AUTOMATION_SCHEDULER_DAEMON';
