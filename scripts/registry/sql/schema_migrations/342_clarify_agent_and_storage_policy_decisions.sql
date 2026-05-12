-- Clarify that model promotion is agent-approved and storage lifecycle is rule-executed, not owner approval prompted.

UPDATE trading_registry
SET payload = 'continuous_safe_work;data_acquisition_to_feature_to_model_to_evaluation_to_promotion_review;autonomous_historical_provider_dispatch;agent_model_promotion_decision;storage_lifecycle_policy_execution;execution_priority_reserved;no_manual_one_task_prompting',
    note = 'Target manager scheduler policy: keep safe historical training and maintenance work progressing automatically across data acquisition, feature generation, model training, evaluation, and promotion-review preparation. Historical provider acquisition is autonomous; model activation is decided by the agent promotion-decision surface; storage lifecycle mutation follows accepted lifecycle/protected-set rules; broker/account mutation remains execution-owned.',
    updated_at = NOW()
WHERE id = 'cfg_MASP001';

UPDATE trading_registry
SET payload = 'pre_promotion_full_training_mode;market_hours_historical_training_backoff_disabled_until_production_model_activation;resource_pressure_gate_still_active;historical_provider_calls_run_autonomously_under_resource_controls;model_activation_requires_agent_promotion_decision;broker_order_fill_account_mutation_still_blocked;reenable_market_hours_protection_before_live_trading',
    note = 'Current pre-promotion scheduler policy: no production model/live trading capacity is active yet, so regular-session market-hours backoff is disabled to prioritize first promotable-model evidence. Host resource gates remain active; historical provider acquisition is autonomous; model activation requires agent promotion decision evidence; broker/execution mutation gates remain hard. Re-enable market-hours protection before production model activation/live trading.',
    updated_at = NOW()
WHERE id = 'cfg_MMHP001';

UPDATE trading_registry
SET note = 'Script-called agent decision artifact used before production model activation. The agent approves, defers, rejects, revokes, or supersedes from evidence; this is not a routine owner approval prompt. Legacy review_decision_v1 artifacts are advisory/evidence scaffolding unless converted through this agent decision boundary.',
    updated_at = NOW()
WHERE id = 'term_AGENTPROMO001';

UPDATE trading_registry
SET note = 'Storage lifecycle policy/agent decision evidence for storage lifecycle mutation. Routine lifecycle work follows accepted policy, protected-set checks, quarantine/recheck rules where applicable, and storage receipts; this is not a human approval prompt.',
    updated_at = NOW()
WHERE id = 'term_STORLIFE001';

UPDATE trading_registry
SET note = 'Builds the script-called agent decision artifact used before production model activation. It has no activation side effects and does not require owner approval by default.',
    updated_at = NOW()
WHERE id = 'scr_MODELPROMO002';

UPDATE trading_registry
SET note = 'Builds storage lifecycle policy/agent decision evidence for lifecycle requests. It has no storage mutation side effects and is not a human approval prompt.',
    updated_at = NOW()
WHERE id = 'scr_STORLIFE002';

UPDATE trading_registry
SET payload = 'model_promotion_no_activation_without_agent_decision;agent_is_decision_actor_not_owner_prompt',
    note = 'Production promotion/activation is decided by a script-called agent from evidence, not by a routine manual owner approval gate.',
    updated_at = NOW()
WHERE id = 'trm_MODELPROMO002';

UPDATE trading_registry
SET note = 'Storage lifecycle maintenance enters normal operation through manager unified requests/task summary. Manager requests, prioritizes, schedules, and observes; lifecycle execution follows accepted policy and protected-set checks; trading-storage owns physical execution and receipts.',
    updated_at = NOW()
WHERE id = 'cfg_SLC008';
