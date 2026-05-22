-- Record the first-model bootstrap exception for promotion readiness.

UPDATE trading_registry
SET payload = 'first_model_bootstrap_allowed_for_initial_promoted_baseline;later_candidates_require_anonymous_incumbent_comparison;promote_is_evaluation_owned;activate_is_execution_shadow_cycle_owned',
    path = 'trading-evaluation/docs/40_promotion_eligibility.md;trading-evaluation/docs/50_promotion_readiness.md;trading-execution/docs/40_runtime_model_lifecycle.md;trading-manager/docs/24_model_promotion.md',
    applies_to = 'trading-evaluation;promotion_eligibility;promotion_readiness;trading-execution;runtime_activation;trading-manager',
    note = 'The first accepted model bundle may be promoted with first_model_bootstrap=true so its own frozen settlement run becomes the bootstrap baseline for future anonymous incumbent comparisons. This admits the model to execution shadow review only; activation still requires execution-owned market-hours shadow-cycle selection and active pointer write gates.',
    updated_at = NOW()
WHERE id = 'cfg_EVALACT001';

UPDATE trading_registry
SET note = 'Evaluation-owned decision stating whether a model candidate is eligible for promotion readiness and execution shadow review. It is based on frozen replay evidence and may use the fixed promotion-evaluation-review skill for advisory agent review. The first accepted model may bootstrap the initial baseline; later candidates require incumbent comparison. It is not runtime activation and has no broker/account side effects.',
    updated_at = NOW()
WHERE id = 'art_EVALPROMO001';

UPDATE trading_registry
SET note = 'Promotion eligibility is judged by vector evidence, not a single score. Comparative model evidence must be blinded after the first promoted baseline exists; first_model_bootstrap may create that initial baseline without activation. If candidate superiority is unclear or identity blinding fails for later candidates, the decision defers or requires shadow evidence rather than active selection.',
    updated_at = NOW()
WHERE id = 'cfg_EVALPROMOREV002';
