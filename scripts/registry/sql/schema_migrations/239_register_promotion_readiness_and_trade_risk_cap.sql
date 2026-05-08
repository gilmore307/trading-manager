-- Register production-promotion readiness and mandatory trade-risk-cap shared contracts.
-- These rows make the accepted manager-phase governance names visible without
-- approving production promotion or live execution.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_MPR001',
    'config',
    'MODEL_PROMOTION_READINESS_CHECKLIST',
    'text',
    'dataset_snapshot_ref;dataset_split_ref;eval_label_refs;eval_run_ref;promotion_metric_refs;promotion_candidate_ref;thresholds_ref;baseline_comparison_ref;split_stability_ref;leakage_check_ref;calibration_report_ref;decision_record_ref',
    'trading-model/docs/95_promotion_readiness.md',
    'model_governance;model_promotion;model_evaluation;production_hardening;layers_1_8',
    'registry_only',
    'Accepted production-promotion readiness checklist for Layers 1-8. Missing evidence or failed gates require a deferred promotion decision; this row does not approve any production promotion.'
  ),
  (
    'cfg_MPR002',
    'config',
    'MODEL_PROMOTION_READINESS_STATUS_MATRIX',
    'text',
    'layer_1_evidence_gated;layer_2_deferred;layer_3_evidence_pending;layer_4_evidence_pending;layer_5_evidence_pending;layer_6_evidence_pending;layer_7_evidence_pending;layer_8_evidence_pending',
    'trading-model/docs/95_promotion_readiness.md',
    'model_governance;model_promotion;production_hardening;layers_1_8',
    'registry_only',
    'Current production-promotion status matrix after model-design closeout. It records that no Layer 1-8 model is approved for production by design closeout alone.'
  ),
  (
    'cfg_TRC001',
    'config',
    'TRADE_RISK_CAP_REQUIRED_FIELDS',
    'text',
    'max_loss_usd;max_loss_pct;time_stop_at;cap_enforcement_mode;cap_failure_action',
    'trading-execution/docs/07_trade_risk_cap.md',
    'trade_risk_cap;decision_record;trading-execution;order_construction;execution_safety',
    'registry_only',
    'Minimum required fields for the execution-side hard trade-risk cap. Direct underlying and long-option premium-defined modes add mode-specific required fields.'
  ),
  (
    'cfg_TRC002',
    'config',
    'TRADE_RISK_CAP_ENFORCEMENT_MODES',
    'text',
    'broker_native_stop;risk_monitor_synthetic_stop;long_option_premium_defined_risk',
    'trading-execution/docs/07_trade_risk_cap.md',
    'trade_risk_cap;trading-execution;order_construction;execution_safety',
    'registry_only',
    'Accepted enforcement-mode vocabulary for mandatory trade-risk-cap validation. Mode naming is shared; broker-specific implementation remains execution-owned.'
  ),
  (
    'cfg_TRC003',
    'config',
    'TRADE_RISK_CAP_FAILURE_POLICY',
    'text',
    'missing_or_invalid_trade_risk_cap_reject_order;cap_failure_action_must_be_reject_order;warn_only_not_allowed',
    'trading-execution/docs/07_trade_risk_cap.md',
    'trade_risk_cap;trading-execution;order_construction;execution_safety',
    'registry_only',
    'Execution safety policy: any missing, malformed, unsupported, stale, or unenforceable trade_risk_cap must reject order construction/placement.'
  ),
  (
    'term_TRC001',
    'term',
    'TRADE_RISK_CAP',
    'text',
    'trade_risk_cap',
    'trading-execution/docs/07_trade_risk_cap.md',
    'decision_record;trading-execution;order_construction;execution_safety;underlying_action_plan;option_expression_plan',
    'registry_only',
    'Shared term for the mandatory pre-order hard risk cap derived from model stop/invalidation thesis or option premium-defined risk. It is not itself a broker order.'
  )
ON CONFLICT (id) DO UPDATE SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note,
  updated_at = NOW();
