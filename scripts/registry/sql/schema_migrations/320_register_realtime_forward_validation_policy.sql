-- Register realtime forward-validation policy and dataset-role boundary.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_RTFV001',
    'config',
    'REALTIME_FORWARD_VALIDATION_POLICY',
    'text',
    'realtime_forward_validation_supplements_not_replaces_initial_historical_splits;append_only_point_in_time_capture_required;frozen_model_config_refs_required;mature_labels_required;no_refit_before_reviewed_snapshot_boundary',
    'trading-manager/docs/100_dataset_expansion.md',
    'trading-manager;trading-model;trading-execution;dataset_expansion;forward_holdout;shadow_monitoring;promotion_review',
    'sync_artifact',
    'Policy for using realtime observations as forward-holdout or shadow-monitoring evidence. Realtime coverage is required for live inference, but initial production promotion still requires chronological historical train/calibration/validation/test evidence unless a reviewed future policy supersedes it.'
  ),
  (
    'trm_RTFV001',
    'term',
    'REALTIME_FORWARD_VALIDATION_DATASET',
    'text',
    'realtime_forward_validation_dataset_v1',
    'trading-model/docs/95_promotion_readiness.md',
    'trading-model;trading-manager;model_dataset_snapshot;model_dataset_split;model_eval_label;model_eval_run;forward_holdout;shadow_monitoring',
    'sync_artifact',
    'Append-only point-in-time realtime evidence captured after model/config freeze for forward validation or shadow monitoring. Rows require mature labels before promotion evidence can use them.'
  ),
  (
    'cfg_RTFV002',
    'config',
    'MODEL_VALIDATION_EVIDENCE_VIEW_POLICY',
    'text',
    'report_historical_broad_sample;report_historical_live_route_simulation;report_realtime_shadow_forward_after_label_maturity;defer_if_missing_baseline_stability_leakage_calibration_context',
    'trading-model/docs/95_promotion_readiness.md',
    'trading-model;promotion_readiness;baseline_comparison;split_stability;leakage_check;calibration_report',
    'sync_artifact',
    'Promotion evidence should keep historical broad-sample, historical live-route simulation, and realtime shadow/forward views separate; missing baseline, stability, leakage, calibration, or dataset context remains a defer condition.'
  ),
  (
    'cfg_RTFV003',
    'config',
    'EXECUTION_REALTIME_CAPTURE_FOR_VALIDATION_BOUNDARY',
    'text',
    'execution_realtime_observations_may_feed_shadow_forward_validation_only_as_append_only_point_in_time_evidence;does_not_authorize_provider_streams_or_broker_mutation',
    'trading-execution/docs/09_realtime_data.md',
    'trading-execution;realtime_market_data;trading-manager;trading-model;no_broker_mutation;no_provider_stream_authorization',
    'sync_artifact',
    'Execution realtime market-data capture may later feed model validation, but catalog/contract registration alone does not open provider streams, call providers, place orders, or replace historical validation splits.'
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
