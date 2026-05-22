-- Preserve existing promotion readiness policy tokens while adding bootstrap semantics.

UPDATE trading_registry
SET payload = 'evaluation_owns_offline_promotion_readiness;execution_owns_runtime_activation;eligible_decision_required;rollback_ref_required;broker_account_mutation_forbidden;first_model_bootstrap_allowed_for_initial_promoted_baseline;later_candidates_require_anonymous_incumbent_comparison',
    updated_at = NOW()
WHERE id = 'cfg_EVALACT001';
