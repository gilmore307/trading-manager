-- Route component-local storage references to trading-storage-owned component roots.

UPDATE trading_registry
SET payload = 'state=/root/projects/trading-storage/storage/manager/runtime/historical_scheduler_state.json;lock=/root/projects/trading-storage/storage/manager/runtime/historical_scheduler.lock;decision_log=/root/projects/trading-storage/storage/manager/runtime/historical_scheduler_decisions.jsonl',
    note = 'Default storage-owned runtime-file layout for the resident historical scheduler: checkpoint state, single-instance lock, and append-only decision JSONL log.',
    updated_at = now()
WHERE key = 'MANAGER_HISTORICAL_SCHEDULER_RUNTIME_FILES';

UPDATE trading_registry
SET payload = '/root/projects/trading-storage/storage/manager/runtime/model_training_workflow_state_YYYY-MM.json',
    note = 'Default storage-owned scheduler checkpoint path for the Layer 1-10 historical-training workflow; component repositories do not own durable storage roots.',
    updated_at = now()
WHERE key = 'MANAGER_MODEL_TRAINING_MONTH_SCOPED_CHECKPOINT';

UPDATE trading_registry
SET payload = replace(payload, '/root/projects/trading-model/storage/runtime/', '/root/projects/trading-storage/storage/model/runtime/'),
    updated_at = now()
WHERE payload LIKE '%/root/projects/trading-model/storage/runtime/%';

UPDATE trading_registry
SET payload = replace(payload, '--data-root /root/projects/trading-data/storage', '--data-root /root/projects/trading-storage/storage/data'),
    updated_at = now()
WHERE key = 'TRADING_EVALUATION_PREPARE_BENCHMARK_DATASET';

UPDATE trading_registry
SET path = replace(path, 'trading-model/storage/', 'trading-storage/storage/model/'),
    updated_at = now()
WHERE path LIKE '%trading-model/storage/%';

