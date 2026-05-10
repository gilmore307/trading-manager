-- Register the safe 2016-01 controlled information pass contract and entrypoint.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_MGRINFO001',
    'artifact_type',
    'MANAGER_CONTROLLED_INFORMATION_PASS_V1',
    'text',
    'manager_controlled_information_pass_v1',
    'trading-manager/docs/101_controlled_information_pass.md',
    'trading-manager;historical_training;dataset_expansion;provider_dispatch;artifact_discovery;storage_lifecycle',
    'sync_artifact',
    'Safe first-month information-gathering report. It may write report/preparation artifacts but performs no provider calls, model activation, broker execution, or storage lifecycle mutation.'
  ),
  (
    'scr_MGRINFO001',
    'script',
    'MANAGER_CONTROLLED_INFORMATION_PASS_PLAN',
    'text',
    'PYTHONPATH=src python3 scripts/tasks/plan_controlled_information_pass.py --start-month 2016-01 --end-month 2016-01',
    'trading-manager/scripts/tasks/plan_controlled_information_pass.py',
    'manager_controlled_information_pass_v1;manager_dataset_expansion_plan_v1;live_call_approval_v1',
    'sync_artifact',
    'Builds the safe controlled information pass report and optional preparation artifacts for 2016-01 without provider calls.'
  ),
  (
    'cfg_MGRINFO001',
    'config',
    'MANAGER_CONTROLLED_INFORMATION_PASS_POLICY',
    'text',
    'start_2016_01;measure_before_widening_defaults;provider_calls_zero;model_activation_false;broker_execution_false;storage_lifecycle_mutation_false;information_topics_provider_concurrency_target_queue_dataset_thresholds_artifact_discovery_storage_lifecycle',
    'trading-manager/docs/101_controlled_information_pass.md',
    'manager_controlled_information_pass_v1;scheduler_defaults;provider_dispatch_defaults;storage_lifecycle_defaults',
    'sync_artifact',
    'Before accepting broad defaults, manager gathers evidence for provider dispatch, concurrency, L3-L7 target queues, dataset thresholds, artifact discovery, and storage lifecycle from the first formal historical month.'
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
