-- Register Layer 1/2 foundation catch-up priority and post-model rebuild boundary.

UPDATE trading_registry
SET payload = CASE
      WHEN payload LIKE '%layer_01_02_foundation_catch_up_priority%' THEN payload
      ELSE payload || ';layer_01_02_foundation_catch_up_priority;post_model_generation_rebuild_boundary'
    END,
    note = 'Manager autonomous scheduler policy: keep continuous safe work and resource-aware execution, prioritize Layer 1/2 historical substrate catch-up to current before ordinary Layer 3+ target work, and treat model-generation-and-later artifacts as rebuild-required after the foundation substrate is current.',
    updated_at = NOW()
WHERE key = 'MANAGER_AUTONOMOUS_SCHEDULER_POLICY';

UPDATE trading_registry
SET note = 'Manager-owned Layer 1-8 workflow plan. During foundation catch-up, Layer 1/2 data_acquisition and feature_generation are the reusable historical substrate; post-feature model stages are blocked for rebuild and Layer 3+ target work waits for catch-up completion.',
    applies_to = CASE
      WHEN applies_to LIKE '%layer_01_02_foundation_catch_up%' THEN applies_to
      ELSE applies_to || ';layer_01_02_foundation_catch_up;post_model_artifact_rebuild_boundary'
    END,
    updated_at = NOW()
WHERE key = 'MANAGER_MODEL_TRAINING_WORKFLOW_PLAN_ARTIFACT';

UPDATE trading_registry
SET note = 'Manager-owned durable workflow state. Month-scoped checkpoints count a foundation catch-up month complete once Layer 1/2 data acquisition and feature generation are succeeded/not_applicable, allowing chronological advancement before target-specific Layer 3+ scheduling.',
    applies_to = CASE
      WHEN applies_to LIKE '%layer_01_02_foundation_catch_up%' THEN applies_to
      ELSE applies_to || ';layer_01_02_foundation_catch_up;historical_substrate_reuse'
    END,
    updated_at = NOW()
WHERE key = 'MANAGER_MODEL_TRAINING_WORKFLOW_STATE';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'term_HIST381A',
    'term',
    'MANAGER_FOUNDATION_CATCH_UP_PRIORITY',
    'text',
    'layer_01_02_foundation_catch_up_priority',
    'trading-manager/src/trading_manager_tasks/model_training_workflow.py',
    'historical_scheduler;model_training_workflow;layer_01_market_regime;layer_02_sector_context',
    'sync_artifact',
    'Scheduler priority policy: catch up Layer 1 market/cross-asset and Layer 2 sector/industry historical substrate from 2016-01 to current before ordinary Layer 3+ target-symbol work.'
  ),
  (
    'term_HIST381B',
    'term',
    'LAYER_01_02_HISTORICAL_CATCH_UP_TO_CURRENT_REQUIRED',
    'text',
    'layer_01_02_historical_catch_up_to_current_required',
    'trading-manager/src/trading_manager_tasks/model_training_workflow.py',
    'workflow_blocker;historical_scheduler;layer_03_plus_target_work',
    'sync_artifact',
    'Workflow blocker used to park ordinary Layer 3+ target-symbol work until Layer 1/2 historical data acquisition and feature generation are caught up to current.'
  ),
  (
    'term_HIST381C',
    'term',
    'POST_MODEL_GENERATION_REBUILD_REQUIRED_AFTER_LAYER_01_02_CATCH_UP',
    'text',
    'post_model_generation_rebuild_required_after_layer_01_02_catch_up',
    'trading-manager/src/trading_manager_tasks/model_training_workflow.py',
    'workflow_blocker;model_generation;model_evaluation;promotion_review_preparation',
    'sync_artifact',
    'Workflow blocker marking model-generation-and-later artifacts as superseded/rebuild-required while the Layer 1/2 historical substrate catches up.'
  ),
  (
    'term_HIST381D',
    'term',
    'HISTORICAL_SUBSTRATE_REUSE_POLICY',
    'text',
    'downloaded_cleaned_feature_substrate_reusable_when_contract_valid',
    'trading-manager/docs/99_historical_scheduler_runtime.md',
    'historical_data;feature_generation;artifact_reuse;layer_01_02_foundation_catch_up',
    'sync_artifact',
    'Downloaded provider data, cleaned rows, and deterministic feature substrate can be reused when point-in-time rules, schema, and source contracts remain valid.'
  ),
  (
    'term_HIST381E',
    'term',
    'POST_MODEL_ARTIFACT_REBUILD_POLICY',
    'text',
    'model_generation_evaluation_promotion_artifacts_superseded_until_rebuilt',
    'trading-manager/docs/99_historical_scheduler_runtime.md',
    'model_generation;model_evaluation;promotion_review;artifact_rebuild;layer_01_02_foundation_catch_up',
    'sync_artifact',
    'Model candidates, evaluation summaries, promotion evidence, and downstream review artifacts created before the accepted Layer 1/2 catch-up policy are not current promotion basis and need rebuild/revalidation after substrate catch-up.'
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
