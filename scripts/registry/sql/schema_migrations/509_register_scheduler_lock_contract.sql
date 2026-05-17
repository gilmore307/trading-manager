-- Register the historical scheduler lock contract used before concurrency expansion.

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
  'trm_SLCK001',
  'term',
  'SCHEDULER_LOCK_CONTRACT',
  'text',
  'scheduler_lock_v1',
  'trading-manager/schemas/scheduler_lock_v1.schema.json',
  'trading-manager;historical_scheduler;scheduler_daemon;provider_partition;stage_reconcile;model_promotion;concurrency_control',
  'sync_artifact',
  'Machine-verifiable lock contract for historical scheduler coordination. Accepted scopes are daemon, month_stage, provider_partition, reconcile, and promotion. Provider partition locks may allow concurrent partition work only; reconcile locks own stage-state transitions. Locks do not authorize broker/account mutation, production model activation, destructive storage lifecycle mutation, or provider calls outside existing scheduler gates.'
),
(
  'cfg_SLCK002',
  'config',
  'SCHEDULER_LOCK_SCOPE_VALUES',
  'text',
  'daemon;month_stage;provider_partition;reconcile;promotion',
  'trading-manager/docs/26_historical_scheduler_runtime.md',
  'scheduler_lock_v1;historical_scheduler;concurrency_control',
  'registry_only',
  'Accepted scheduler lock scopes. Daemon is the process guard; month_stage protects one workflow transition lane; provider_partition protects one provider worker partition; reconcile owns receipt reconciliation and stage-state advancement; promotion protects one model-candidate review lane.'
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
