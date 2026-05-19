-- Clean remaining active registry text after moving activation ownership to trading-evaluation.

UPDATE trading_registry
SET applies_to = 'model_promotion_review;promotion_eligibility;model_activation;storage_lifecycle_request;trading-evaluation;trading-storage',
    note = 'Evaluation may classify promoted-model artifact retention intent and mark promoted model bodies/lineage keep-forever. Storage lifecycle execution remains storage-owned with protected-set checks and receipts.',
    updated_at = NOW()
WHERE key = 'PROMOTION_STORAGE_LIFECYCLE_BOUNDARY_POLICY';

UPDATE trading_registry
SET payload = 'pre_promotion_full_training_mode;market_hours_historical_training_backoff_disabled_until_evaluation_model_activation;resource_pressure_gate_still_active;historical_provider_calls_run_autonomously_under_resource_controls;model_activation_requires_evaluation_activation_record;broker_order_fill_account_mutation_still_blocked;reenable_market_hours_protection_before_live_trading',
    note = 'Current pre-promotion scheduler policy: no production model/live trading capacity is active yet, so regular-session market-hours backoff is disabled to prioritize first promotable-model evidence. Host resource gates remain active; historical provider acquisition is autonomous; model activation requires evaluation-owned activation evidence; broker/execution mutation gates remain hard. Re-enable market-hours protection before production model activation/live trading.',
    updated_at = NOW()
WHERE key = 'MANAGER_MARKET_HOURS_HISTORICAL_PAUSE_POLICY';

UPDATE trading_registry
SET note = 'One scheduler tick decision artifact: records allowed/backoff/executed status, resource gate state, selected work, next internal stage, command preview, and safety counters. Historical provider acquisition can advance automatically; evaluation activation and broker/execution mutation remain separate and false unless their own gates pass.',
    updated_at = NOW()
WHERE key = 'MANAGER_SCHEDULER_DECISION';
