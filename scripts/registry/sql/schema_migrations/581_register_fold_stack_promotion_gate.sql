-- Require full Layer 1-9 fold-stack evaluation before promotion review can run.

UPDATE trading_registry
SET payload = 'candidate_ref_required;evaluation_run_refs_optional;evidence_refs_optional;fold_layers_01_09_model_evaluation_complete_required;manager_schedules_only;evaluation_owns_benchmark_settlement_eligibility_readiness;execution_owns_shadow_cycle_activation',
    note = 'Manager prepares and schedules model promotion/evaluation/execution-review requests. Promotion review is fold-stack scoped: single-layer fold evaluation is diagnostic only until Layer 1 through Layer 9 model_evaluation stages complete for the same fold. Benchmark judgment and promotion readiness belong to trading-evaluation; live/shadow runtime active selection belongs to trading-execution.',
    updated_at = NOW()
WHERE key = 'MODEL_PROMOTION_UNIFIED_REVIEW_POLICY';

UPDATE trading_registry
SET payload = 'data_acquisition_and_feature_generation_are_month_scoped;model_generation_and_model_evaluation_are_fold_scoped;promotion_review_waits_for_fold_layers_01_09_model_evaluation_complete',
    note = 'Month Ingest Workers own single-month substrate stages: data_acquisition and feature_generation/input preparation. Model Worker 1 owns fold-scoped model_generation and model_evaluation. Promotion review is blocked until the same fold has completed Layer 1 through Layer 9 model_evaluation; single-layer fold results are diagnostic until the full stack closes.',
    updated_at = NOW()
WHERE key = 'MONTHLY_SUBSTRATE_FOLD_MODEL_STAGE_BOUNDARY';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_FOLDPROMO001',
    'config',
    'FOLD_STACK_PROMOTION_GATE_POLICY',
    'text',
    'fold_layers_01_09_model_evaluation_complete_required_before_promotion_review',
    'trading-manager/src/trading_manager_tasks/model_training_workflow.py;trading-manager/docs/24_model_promotion.md;trading-evaluation/docs/30_fold_settlement.md',
    'historical_scheduler;model_training_workflow;fold_settlement;promotion_review;layers_1_9',
    'sync_artifact',
    'Promotion review is not triggered by one model completing one fold. It opens only after Layer 1 through Layer 9 model_evaluation stages have completed for the same fold, so evaluation judges a complete stack rather than a partial upstream/downstream state.'
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
