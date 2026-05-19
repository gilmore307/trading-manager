-- Clean stale evaluation-activation wording after runtime activation moved to execution.

UPDATE trading_registry
SET note = 'One scheduler tick decision artifact: records allowed/backoff/executed status, resource gate state, selected work, next internal stage, command preview, and safety counters. Historical provider acquisition can advance automatically; runtime model selection and broker/execution mutation remain separate and false unless their own gates pass.',
    updated_at = NOW()
WHERE key = 'MANAGER_SCHEDULER_DECISION';

UPDATE trading_registry
SET applies_to = 'trading-evaluation;promotion_eligibility;model_promotion;promotion_readiness',
    note = 'Evaluation-owned decision stating whether a model candidate is eligible for promotion readiness and execution shadow review. It is based on frozen benchmark evidence and may use the fixed promotion-evaluation-review skill for advisory agent review; it is not runtime activation and has no broker/account side effects.',
    updated_at = NOW()
WHERE key = 'PROMOTION_ELIGIBILITY_DECISION';

UPDATE trading_registry
SET note = 'Generic manager advisory review decision artifact. It may inform evaluation/execution review, but it cannot activate configs; runtime active model selection belongs to trading-execution.',
    updated_at = NOW()
WHERE key = 'REVIEW_DECISION_ARTIFACT';

UPDATE trading_registry
SET applies_to = 'model_promotion_review;advisory_evidence;trading-manager;trading-evaluation;trading-execution',
    note = 'Script-called agent decision artifact retained as advisory evaluation/execution evidence. It does not own activation; trading-evaluation owns promotion eligibility/readiness and trading-execution owns runtime active model selection.',
    updated_at = NOW()
WHERE key = 'AGENT_MODEL_PROMOTION_DECISION';

UPDATE trading_registry
SET note = 'Promotion evidence should keep historical broad-sample, historical live-route simulation, and realtime shadow/forward views separate; missing baseline, stability, leakage, calibration, or dataset context remains a defer condition. Runtime activation remains execution-owned.',
    updated_at = NOW()
WHERE key = 'MODEL_VALIDATION_EVIDENCE_VIEW_POLICY';

UPDATE trading_registry
SET payload = 'pre_promotion_full_training_mode;market_hours_historical_training_backoff_disabled_until_execution_runtime_activation;resource_pressure_gate_still_active;historical_provider_calls_run_autonomously_under_resource_controls;runtime_activation_requires_execution_shadow_cycle_selection;broker_order_fill_account_mutation_still_blocked;reenable_market_hours_protection_before_live_trading',
    note = 'Current pre-promotion scheduler policy: no production model/live trading capacity is active yet, so regular-session market-hours backoff is disabled to prioritize first promotable-model evidence. Host resource gates remain active; historical provider acquisition is autonomous; runtime active selection requires execution-owned shadow-cycle evidence; broker/execution mutation gates remain hard. Re-enable market-hours protection before production runtime activation/live trading.',
    updated_at = NOW()
WHERE key = 'MANAGER_MARKET_HOURS_HISTORICAL_PAUSE_POLICY';
