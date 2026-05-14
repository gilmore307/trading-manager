-- Correct the accepted stage payload to Promotion Review after replacing preparation wording.

UPDATE trading_registry
SET applies_to = replace(applies_to, 'promotion_review_preparation', 'promotion_review'),
    note = replace(replace(note, 'promotion-review preparation', 'Promotion Review'), 'promotion task', 'Promotion Review task'),
    updated_at = NOW()
WHERE applies_to LIKE '%promotion_review_preparation%'
   OR note LIKE '%promotion-review preparation%'
   OR note LIKE '%promotion task%';

UPDATE trading_registry
SET payload = 'promotion_review',
    note = 'Scheduler stage type for the complete fold-scoped Promotion Review task: evidence packet, gates, baseline comparison, split stability, leakage/calibration/test report, agent decision, and durable decision write.',
    updated_at = NOW()
WHERE key = 'PROMOTION_STAGE_TYPE';

UPDATE trading_registry
SET note = 'During Layer 1/2 foundation catch-up, month-scoped workflow state must not expose per-month model_generation, model_evaluation, promotion_review, or maintenance stages; model/promotion work is fold-scoped.',
    updated_at = NOW()
WHERE key = 'MONTH_SCOPED_INGEST_ONLY_DURING_FOUNDATION_CATCH_UP';

UPDATE trading_registry
SET note = 'Manager-owned Layer 1-8 workflow plan. During foundation catch-up, Layer 1/2 month-scoped workflow states expose only data_acquisition and feature_generation; model generation/evaluation/Promotion Review belong to fold-scoped model/promotion work after frozen 4+1+1 manifests exist.',
    updated_at = NOW()
WHERE key = 'MANAGER_MODEL_TRAINING_WORKFLOW_PLAN_ARTIFACT';
