-- Register realtime decision-effectiveness monitoring policy.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_RTEM001',
    'term',
    'REALTIME_MODEL_DECISION_EFFECTIVENESS',
    'text',
    'realtime_model_decision_effectiveness_v1',
    'trading-execution/docs/09_realtime_data.md',
    'trading-execution;realtime_monitoring;model_decision_quality;accuracy;hit_rate;mature_outcome_labels;not_historical_test_rows',
    'sync_artifact',
    'Lightweight online monitoring surface for whether live/shadow model decisions were correct after their outcome horizon matured. It records decision/config refs, outcome refs, correctness status, and aggregate effectiveness metrics without building historical test rows.'
  ),
  (
    'cfg_RTEM001',
    'config',
    'REALTIME_DECISION_EFFECTIVENESS_POLICY',
    'text',
    'realtime_monitoring_records_model_decision_correctness_metrics_not_historical_train_test_or_forward_holdout_rows;historical_backfill_owns_reviewed_dataset_snapshots_and_splits',
    'trading-manager/docs/100_dataset_expansion.md',
    'trading-manager;trading-execution;realtime_monitoring;historical_dataset_boundary;promotion_review;drift_review',
    'sync_artifact',
    'Policy that realtime monitoring should measure model decision correctness with lightweight online metrics. Realtime monitor output may inform promotion/drift/retraining review, but does not become historical test/holdout/training rows by default because historical backfill owns those dataset splits.'
  ),
  (
    'trm_RTEM002',
    'term',
    'REALTIME_EFFECTIVENESS_OUTCOME_LABEL',
    'text',
    'realtime_effectiveness_outcome_label_v1',
    'trading-execution/docs/09_realtime_data.md',
    'trading-execution;realtime_model_decision_effectiveness_v1;label_maturity;outcome_horizon;correctness_status',
    'sync_artifact',
    'Matured outcome label/ref used to score a realtime live or shadow model decision for lightweight effectiveness monitoring.'
  ),
  (
    'cfg_RTEM002',
    'config',
    'REALTIME_MONITORING_NO_HISTORICAL_TESTSET_POLICY',
    'text',
    'do_not_use_realtime_monitoring_as_default_historical_testset_or_forward_holdout_generator;avoid_heavy_historical_dataset_processing_in_realtime_monitor',
    'trading-execution/docs/09_realtime_data.md',
    'trading-execution;realtime_monitoring;runtime_load_control;historical_pipeline_boundary',
    'sync_artifact',
    'Realtime monitor load-control policy: avoid heavy historical-dataset processing and default test-set generation in the live monitor; historical backfill will catch up through the normal data/model pipeline.'
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
