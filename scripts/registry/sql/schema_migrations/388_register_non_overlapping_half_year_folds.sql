-- Correct Model Worker fold cadence from monthly rolling windows to non-overlapping half-year folds.

UPDATE trading_registry
SET payload = '6',
    applies_to = 'historical_scheduler;model_worker_1;fold_step;non_overlapping_half_year_fold',
    note = 'Accepted step between Model Worker folds. Folds are non-overlapping half-year groups: 2016-01..2016-06, then 2016-07..2016-12, not monthly sliding windows such as 2016-02..2016-07.',
    updated_at = NOW()
WHERE key = 'TRADING_MANAGER_ROLLING_FOLD_STEP_MONTHS';

UPDATE trading_registry
SET payload = 'non_overlapping_half_year_folds',
    applies_to = 'historical_scheduler;model_worker_1;fold_scope;four_one_one_split',
    note = 'Model Worker fold cadence uses non-overlapping six-month groups: 01-06 then 07-12. The 4+1+1 train/validation/test split occurs inside each half-year fold; overlapping monthly rolling folds are not active runtime behavior.',
    updated_at = NOW()
WHERE key = 'ROLLING_FOLD_PROMOTION_RUNTIME';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
    'cfg_FOLDSTEP001',
    'config',
    'MODEL_WORKER_NON_OVERLAPPING_HALF_YEAR_FOLDS',
    'text',
    '2016-01..2016-06;2016-07..2016-12;step_months=6',
    'trading-manager/src/trading_manager_tasks/scheduler_daemon.py;trading-manager/docs/99_historical_scheduler_runtime.md',
    'historical_scheduler;model_worker_1;fold_selection;four_one_one_split',
    'sync_artifact',
    'Model Worker 1 selects complete non-overlapping six-month folds. After fold_2016-01_2016-06 is complete, the next eligible fold is fold_2016-07_2016-12; overlapping fold_2016-02_2016-07 is invalid.'
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
