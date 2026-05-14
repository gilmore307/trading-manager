-- Register fold-scoped promotion stage semantics and remove old preparation wording.

UPDATE trading_registry
SET applies_to = replace(applies_to, 'promotion_review_preparation', 'promotion'),
    note = replace(note, 'promotion-review preparation', 'promotion'),
    updated_at = NOW()
WHERE applies_to LIKE '%promotion_review_preparation%'
   OR note LIKE '%promotion-review preparation%';

UPDATE trading_registry
SET note = 'Manager-owned Layer 1-8 workflow plan. During foundation catch-up, Layer 1/2 month-scoped workflow states expose only data_acquisition and feature_generation; model generation/evaluation/promotion belong to fold-scoped model/promotion work after frozen 4+1+1 manifests exist.',
    applies_to = CASE
      WHEN applies_to LIKE '%rolling_fold_promotion%' THEN applies_to
      ELSE applies_to || ';rolling_fold_promotion;four_one_one_split'
    END,
    updated_at = NOW()
WHERE key = 'MANAGER_MODEL_TRAINING_WORKFLOW_PLAN_ARTIFACT';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'term_RF382A',
    'term',
    'PROMOTION_STAGE_TYPE',
    'text',
    'promotion',
    'trading-manager/src/trading_manager_tasks/model_training_workflow.py',
    'historical_scheduler;model_promotion_worker;rolling_fold_promotion;stage_type',
    'sync_artifact',
    'Scheduler stage type for the complete fold-scoped promotion task: evidence packet, gates, baseline comparison, split stability, leakage/calibration/test report, agent decision, and durable decision write.'
  ),
  (
    'term_RF382B',
    'term',
    'ROLLING_FOLD_FOUR_ONE_ONE_SPLIT',
    'text',
    'train_months=4;validation_months=1;test_months=1;fold_size_months=6',
    'trading-manager/docs/98_automation_scheduler.md',
    'rolling_fold_promotion;model_promotion_worker;dataset_split_policy',
    'sync_artifact',
    'Accepted rolling-fold split policy: four training months, one validation month, and one test month per six-month frozen fold manifest.'
  ),
  (
    'term_RF382C',
    'term',
    'MONTH_SCOPED_INGEST_ONLY_DURING_FOUNDATION_CATCH_UP',
    'text',
    'month_scoped_layer_01_02_workflow_exposes_data_acquisition_and_feature_generation_only',
    'trading-manager/src/trading_manager_tasks/model_training_workflow.py',
    'historical_scheduler;layer_01_02_foundation_catch_up;month_ingest_worker',
    'sync_artifact',
    'During Layer 1/2 foundation catch-up, month-scoped workflow state must not expose per-month model_generation, model_evaluation, promotion, or maintenance stages; model/promotion work is fold-scoped.'
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
