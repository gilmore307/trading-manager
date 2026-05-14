-- Register the rolling-fold promotion runtime charter accepted after pausing monthly scheduler progression.
-- Manager remains the control plane; activation, broker/account mutation, and live trading stay outside this policy.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'term_RFP001',
    'term',
    'ROLLING_FOLD_PROMOTION_RUNTIME',
    'text',
    'rolling_fold_promotion',
    'trading-manager/docs/81_decision.md;trading-manager/docs/98_automation_scheduler.md',
    'historical_scheduler;model_training;model_promotion;rolling_fold',
    'sync_artifact',
    'Accepted historical runtime charter: month-scoped ingest workers prepare reusable substrate, while one serial model/promotion worker consumes frozen rolling-fold manifests and owns model/evaluation/promotion decision tasks.'
  ),
  (
    'term_RFP002',
    'term',
    'MONTH_INGEST_WORKER',
    'text',
    'month_ingest_worker',
    'trading-manager/docs/81_decision.md;trading-manager/docs/98_automation_scheduler.md',
    'historical_scheduler;data_acquisition;feature_generation;monthly_substrate',
    'sync_artifact',
    'Bounded worker lane that prepares month-scoped provider/raw data, cleaned data, point-in-time features, feature-ready manifests, and coverage evidence.'
  ),
  (
    'term_RFP003',
    'term',
    'MODEL_PROMOTION_WORKER',
    'text',
    'model_promotion_worker',
    'trading-manager/docs/81_decision.md;trading-manager/docs/98_automation_scheduler.md',
    'historical_scheduler;model_generation;model_evaluation;model_promotion',
    'sync_artifact',
    'Serial worker lane that consumes complete frozen fold manifests and owns model generation, validation/calibration, test evaluation, promotion evidence, and agent decision tasks.'
  ),
  (
    'term_RFP004',
    'term',
    'FROZEN_ROLLING_FOLD_INPUT_MANIFEST',
    'text',
    'frozen_rolling_fold_input_manifest',
    'trading-manager/docs/81_decision.md;trading-manager/docs/98_automation_scheduler.md',
    'historical_scheduler;rolling_fold;model_worker;input_manifest;ready_signal',
    'sync_artifact',
    'Versioned explicit manifest consumed by the model/promotion worker; it freezes fold input artifacts, ready signals, coverage evidence, and split scope so model work never reads unqualified latest or partial staging rows.'
  ),
  (
    'term_RFP005',
    'term',
    'ROLLING_FOLD_PROMOTION_TASK',
    'text',
    'rolling_fold_promotion_task',
    'trading-manager/docs/81_decision.md;trading-manager/docs/98_automation_scheduler.md',
    'historical_scheduler;promotion_task;agent_model_promotion_decision;model_governance',
    'sync_artifact',
    'One scheduler task packaging evidence packet build, gate checks, baseline comparison, split stability, leakage check, calibration/test report, agent review, and durable promotion decision write.'
  ),
  (
    'term_RFP006',
    'term',
    'PROMOTION_NOT_ACTIVATION_POLICY',
    'text',
    'promotion_not_activation',
    'trading-manager/docs/81_decision.md;trading-manager/docs/98_automation_scheduler.md;trading-manager/docs/96_model_promotion.md',
    'model_promotion;activation_boundary;broker_account_boundary;historical_scheduler',
    'sync_artifact',
    'Promotion approval does not activate a live model, switch production pointers, submit orders, mutate accounts, or authorize live trading; activation remains a separate reviewed policy boundary.'
  ),
  (
    'cfg_RFP001',
    'config',
    'TRADING_MANAGER_MONTH_INGEST_WORKERS',
    'text',
    '4',
    'trading-manager/docs/81_decision.md;trading-manager/docs/98_automation_scheduler.md',
    'historical_scheduler;month_ingest_worker;worker_count',
    'sync_artifact',
    'Accepted count of parallel month-ingest worker lanes for the next rolling-fold historical runtime.'
  ),
  (
    'cfg_RFP002',
    'config',
    'TRADING_MANAGER_MODEL_PROMOTION_WORKERS',
    'text',
    '1',
    'trading-manager/docs/81_decision.md;trading-manager/docs/98_automation_scheduler.md',
    'historical_scheduler;model_promotion_worker;worker_count;serial_execution',
    'sync_artifact',
    'Accepted count of serial model/promotion worker lanes; model generation, evaluation, and promotion decisions must not run as competing parallel workers.'
  ),
  (
    'cfg_RFP003',
    'config',
    'TRADING_MANAGER_ROLLING_FOLD_SIZE_MONTHS',
    'text',
    '6',
    'trading-manager/docs/81_decision.md;trading-manager/docs/98_automation_scheduler.md',
    'historical_scheduler;rolling_fold;split_policy',
    'sync_artifact',
    'Accepted rolling fold size in months for production-grade promotion evidence.'
  ),
  (
    'cfg_RFP004',
    'config',
    'TRADING_MANAGER_ROLLING_FOLD_TRAIN_MONTHS',
    'text',
    '4',
    'trading-manager/docs/81_decision.md;trading-manager/docs/98_automation_scheduler.md',
    'historical_scheduler;rolling_fold;train_split',
    'sync_artifact',
    'Accepted number of train months in each six-month rolling fold.'
  ),
  (
    'cfg_RFP005',
    'config',
    'TRADING_MANAGER_ROLLING_FOLD_VALIDATION_MONTHS',
    'text',
    '1',
    'trading-manager/docs/81_decision.md;trading-manager/docs/98_automation_scheduler.md',
    'historical_scheduler;rolling_fold;validation_split;calibration_split',
    'sync_artifact',
    'Accepted number of validation/calibration months in each six-month rolling fold.'
  ),
  (
    'cfg_RFP006',
    'config',
    'TRADING_MANAGER_ROLLING_FOLD_TEST_MONTHS',
    'text',
    '1',
    'trading-manager/docs/81_decision.md;trading-manager/docs/98_automation_scheduler.md',
    'historical_scheduler;rolling_fold;test_split',
    'sync_artifact',
    'Accepted number of test months in each six-month rolling fold.'
  ),
  (
    'cfg_RFP007',
    'config',
    'TRADING_MANAGER_ROLLING_FOLD_STEP_MONTHS',
    'text',
    '1',
    'trading-manager/docs/81_decision.md;trading-manager/docs/98_automation_scheduler.md',
    'historical_scheduler;rolling_fold;fold_step',
    'sync_artifact',
    'Default month step between rolling folds.'
  ),
  (
    'sts_RFP001',
    'status_value',
    'ROLLING_FOLD_PROMOTION_RESULT_APPROVED',
    'status_value',
    'approved',
    'trading-manager/docs/81_decision.md;trading-manager/docs/98_automation_scheduler.md',
    'rolling_fold_promotion_task;promotion_result;agent_model_promotion_decision',
    'sync_artifact',
    'Scheduler-level rolling-fold promotion result meaning the model candidate passed promotion review; it still does not activate live trading by itself.'
  ),
  (
    'sts_RFP002',
    'status_value',
    'ROLLING_FOLD_PROMOTION_RESULT_DEFERRED',
    'status_value',
    'deferred',
    'trading-manager/docs/81_decision.md;trading-manager/docs/98_automation_scheduler.md',
    'rolling_fold_promotion_task;promotion_result;agent_model_promotion_decision',
    'sync_artifact',
    'Scheduler-level rolling-fold promotion result meaning evidence is insufficient or gates remain open; no activation or pointer switch is allowed.'
  ),
  (
    'sts_RFP003',
    'status_value',
    'ROLLING_FOLD_PROMOTION_RESULT_REJECTED',
    'status_value',
    'rejected',
    'trading-manager/docs/81_decision.md;trading-manager/docs/98_automation_scheduler.md',
    'rolling_fold_promotion_task;promotion_result;agent_model_promotion_decision',
    'sync_artifact',
    'Scheduler-level rolling-fold promotion result meaning the candidate failed promotion review; no activation or pointer switch is allowed.'
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
