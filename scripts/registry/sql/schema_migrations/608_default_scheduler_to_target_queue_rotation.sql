-- Default the historical scheduler service to queue-driven Layer 3+ target rotation.

UPDATE trading_registry
SET payload = 'target_queue_driven_by_default',
    path = 'trading-manager/deploy/systemd/trading-manager-historical-scheduler.env;trading-manager/deploy/systemd/trading-manager-historical-scheduler.service;trading-manager/docs/25_automation_scheduler.md;trading-manager/docs/26_historical_scheduler_runtime.md',
    applies_to = 'historical_scheduler;model_training_workflow;target_queue;target_rotation;layer_03_plus',
    note = 'The checked-in historical scheduler service no longer pins TRADING_MANAGER_SELECTED_TARGET_SYMBOL by default. Layer 3+ model-worker training reads runtime/model_training_target_queue.json and rotates to the first target with an open or unstarted eligible fold. A reviewed service override may still pass --target-symbol for a one-target repair run.',
    updated_at = NOW()
WHERE id = 'cfg_DU002';

UPDATE trading_registry
SET note = 'Runs the persistent historical-training automation scheduler daemon. The checked-in service path is queue-driven for Layer 3+ target rotation: when --target-symbol is omitted, the daemon reads runtime/model_training_target_queue.json and starts the next target from its earliest open eligible fold after prior targets catch up.',
    applies_to = 'trading-manager;historical_scheduler;model_worker;target_rotation;target_queue;month_ingest_worker_lanes;dashboard_refresh',
    updated_at = NOW()
WHERE key = 'RUN_AUTOMATION_SCHEDULER_DAEMON';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
    'scr_MGRTRGROT001',
    'script',
    'PREPARE_MODEL_WORKER_TARGET_QUEUE',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/prepare_model_worker_target_queue.py --write',
    'trading-manager/scripts/tasks/prepare_model_worker_target_queue.py',
    'trading-manager;historical_scheduler;model_worker;target_queue;target_rotation',
    'sync_artifact',
    'Builds runtime/model_training_target_queue.json from the reviewed bootstrap target and accepted target-context mapping rows. The queue is scheduler routing evidence only and not promotion evidence.'
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
