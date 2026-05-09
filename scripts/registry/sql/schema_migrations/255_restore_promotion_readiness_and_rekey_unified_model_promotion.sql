-- Restore production-promotion readiness rows overwritten by migration 254 id reuse
-- and move unified model-promotion config rows onto non-conflicting ids.

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
    'layer_1_evidence_gated;layer_2_deferred;layer_3_evidence_pending;layer_4_evidence_pending;layer_5_evidence_pending;layer_6_evidence_pending;layer_7_evidence_pending;layer_8_evidence_pending;layer_1_deferred_after_real_evaluation;layer_3_real_production_eval_substrate_deferred_upstream_dependencies_and_calibration;layer_8_agent_reviewed_deferred_no_production_eval_substrate',
    'trading-model/docs/95_promotion_readiness.md',
    'model_governance;model_promotion;production_hardening;layers_1_8',
    'registry_only',
    'Current production-promotion status matrix after model-design closeout. It records that no Layer 1-8 model is approved for production by design closeout alone.'
  ),
  (
    'cfg_UMP001',
    'config',
    'MODEL_PROMOTION_UNIFIED_REVIEW_POLICY',
    'text',
    'candidate_ref_required;evaluation_run_refs_optional;evidence_refs_optional;activation_requires_approved_review_decision;deferred_rejected_failed_partial_must_not_activate',
    'trading-manager/docs/96_model_promotion.md',
    'model_promotion_review_v1;review_decision_v1;activation_record_v1;promotion_control_plane',
    'sync_artifact',
    'Shared manager policy for the unified model-promotion review entrypoint. A request may ask for review, but activation is valid only after an approving review decision.'
  ),
  (
    'cfg_UMP002',
    'config',
    'MODEL_PROMOTION_UNIFIED_TARGETS',
    'text',
    'model_01_market_regime;model_02_sector_context;model_03_target_state_vector;model_04_event_overlay;model_05_alpha_confidence;model_06_position_projection;model_07_underlying_action;model_08_option_expression',
    'trading-manager/docs/96_model_promotion.md',
    'model_promotion_review_v1;layers_1_8;promotion_control_plane',
    'sync_artifact',
    'Model ids accepted by the unified manager-side promotion review request planner.'
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
