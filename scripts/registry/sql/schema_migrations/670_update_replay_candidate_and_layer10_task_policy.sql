-- Align active registry policy with the current model research run cycle.

UPDATE trading_registry
SET key = 'MODEL_REPLAY_CANDIDATE_SELECTION_POLICY',
    payload = 'target_substrate_does_not_select_replay_targets_components_choose_candidates_or_combinations',
    path = 'trading-manager/src/trading_manager_tasks/model_training_workflow.py;trading-manager/docs/02_architecture.md;trading-manager/docs/05_decision.md',
    applies_to = 'historical_scheduler;model_training_workflow;model_group_replay;candidate_pool;target_substrate',
    note = 'Target-major substrate work prepares data samples only. Promotion replay runs the live-flow component graph over the historical point-in-time candidate pool, allowing components to choose no target, one target, or a target combination. Fixed target/window panels are diagnostic repair evidence only and are not accepted promotion evidence.',
    updated_at = NOW()
WHERE id = 'cfg_L4SINGLETARGET001';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_L10POSTREPLAY001',
    'config',
    'LAYER_10_POST_REPLAY_ATTRIBUTION_POLICY',
    'text',
    'layer_10_starts_after_concentrated_replay_not_before_replay_input_stage',
    'trading-manager/src/trading_manager_tasks/model_training_workflow.py;trading-manager/docs/20_task_system.md;trading-manager/docs/26_historical_scheduler_runtime.md',
    'historical_scheduler;model_training_workflow;model_group_replay;layer_10_event_risk_governor;failure_attribution',
    'sync_artifact',
    'Layer 10 starts after concentrated live-flow replay exposes failures, residuals, misses, or deviations. It must not run as a pre-replay data-acquisition or feature-generation stage.'
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

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_L4FOLDEVENT001',
    'config',
    'LAYER_4_FOLD_EVENT_OBSERVATION_POLICY',
    'text',
    'layer_4_global_sector_event_observation_substrate_collected_each_fold',
    'trading-manager/src/trading_manager_tasks/model_training_workflow.py;trading-manager/docs/20_task_system.md;trading-manager/docs/25_automation_scheduler.md',
    'historical_scheduler;model_training_workflow;layer_04_event_failure_risk;event_observation_pool;foundation_substrate',
    'sync_artifact',
    'Layer 4 global and sector event-observation substrate is collected for each fold because the accepted event observation pool can change across folds. It remains reusable across target research runs inside that fold.'
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
