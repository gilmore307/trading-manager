-- Register the read-only scheduler lock plan surfaced by dry-run decisions and status.

INSERT INTO trading_registry (
  id,
  kind,
  key,
  payload_format,
  payload,
  path,
  applies_to,
  artifact_sync_policy,
  note
) VALUES (
  'trm_SLCK003',
  'term',
  'SCHEDULER_LOCK_PLAN',
  'text',
  'scheduler_lock_plan_v1',
  'trading-manager/src/trading_manager_tasks/scheduler_locks.py',
  'trading-manager;historical_scheduler;manager_scheduler_decision;manager_historical_scheduler_status;scheduler_lock_v1;dry_run_planning;observability',
  'sync_artifact',
  'Read-only lock planning surface emitted by dry-run scheduler decisions and historical scheduler status. It lists daemon/stage/reconcile lock refs and provider-partition lock templates required for selected work without acquiring locks, starting workers, calling providers, advancing workflow state, activating models, mutating broker/account state, or mutating storage lifecycle.'
)
ON CONFLICT (id) DO UPDATE SET
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note,
  updated_at = NOW();

UPDATE trading_registry
SET note = 'Machine-verifiable lock contract for historical scheduler coordination. Accepted scopes are daemon, month_stage, provider_partition, reconcile, and promotion. Provider partition locks may allow concurrent partition work only; reconcile locks own stage-state transitions. Dry-run decisions and status snapshots expose scheduler_lock_plan_v1 before worker launch. Locks do not authorize broker/account mutation, production model activation, destructive storage lifecycle mutation, or provider calls outside existing scheduler gates.',
    updated_at = NOW()
WHERE id = 'trm_SLCK001';
