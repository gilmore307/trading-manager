-- Register the single manager-side entrypoint for all model promotion review requests.
-- Model repositories remain evidence producers; manager owns the shared request,
-- review decision, and activation-control boundary.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'req_MPR001',
    'request_type',
    'MODEL_PROMOTION_REVIEW_V1',
    'text',
    'model_promotion_review_v1',
    'trading-manager/docs/96_model_promotion.md',
    'manager_request_v1;model_promotion;promotion_review;layers_1_8;trading-manager;trading-model',
    'sync_artifact',
    'Single manager-side request type for reviewing promotion candidates across every model layer. Layer-specific differences belong in evidence adapters, metrics, labels, baselines, and gate policies, not separate promotion mechanisms.'
  ),
  (
    'cfg_MPR001',
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
    'cfg_MPR002',
    'config',
    'MODEL_PROMOTION_UNIFIED_TARGETS',
    'text',
    'model_01_market_regime;model_02_sector_context;model_03_target_state_vector;model_04_event_overlay;model_05_alpha_confidence;model_06_position_projection;model_07_underlying_action;model_08_option_expression',
    'trading-manager/docs/96_model_promotion.md',
    'model_promotion_review_v1;layers_1_8;promotion_control_plane',
    'sync_artifact',
    'Model ids accepted by the unified manager-side promotion review request planner.'
  ),
  (
    'scr_MPR001',
    'script',
    'MANAGER_MODEL_PROMOTION_REVIEW_PLAN',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/plan_model_promotion_review.py',
    '/root/projects/trading-manager/scripts/tasks/plan_model_promotion_review.py',
    'model_promotion_review_v1;manager_request_v1;promotion_review;layers_1_8;trading-manager',
    'sync_artifact',
    'Stable callable manager entrypoint for planning unified model-promotion review requests. It emits manager_request_v1 rows and does not compute model metrics or approve activation.'
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
