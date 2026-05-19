-- Finish promotion/activation wording cleanup after activation moved to execution runtime lifecycle.

UPDATE trading_registry
SET applies_to = 'manager_request;model_promotion;trading-evaluation;fold_settlement;promotion_eligibility;promotion_readiness;trading-execution;runtime_activation',
    note = 'Single manager-side request type for scheduling evaluation-owned promotion readiness work and execution-owned runtime shadow-cycle review across every model layer.',
    updated_at = NOW()
WHERE key = 'MODEL_PROMOTION_REVIEW';

UPDATE trading_registry
SET applies_to = 'agent_model_promotion_decision;model_promotion_review;promotion_readiness;agent_decision_evidence',
    note = 'Builds the script-called agent decision artifact used as advisory evidence before promotion readiness or runtime shadow-cycle selection. It has no activation side effects and does not require owner approval by default.',
    updated_at = NOW()
WHERE key = 'BUILD_AGENT_MODEL_PROMOTION_DECISION';

UPDATE trading_registry
SET applies_to = 'model_promotion_review;advisory_evidence;trading-manager;trading-evaluation;trading-execution',
    note = 'Manager-side helper for advisory review_decision artifacts only. It has no activation side effects; promotion readiness belongs to trading-evaluation and runtime active selection belongs to trading-execution.',
    updated_at = NOW()
WHERE key = 'MANAGER_REVIEW_DECISION_BUILD';

UPDATE trading_registry
SET note = 'Validate an evaluation benchmark contract JSON file. The validator has no provider calls, SQL mutation, storage lifecycle mutation, runtime activation, broker execution, or account mutation.',
    updated_at = NOW()
WHERE key = 'TRADING_EVALUATION_VALIDATE_BENCHMARK_CONTRACT';

UPDATE trading_registry
SET payload = 'formal_realtime_provider_observe_requires_realtime_live_observe_approval;manager_control_plane_rows_may_persist_only_on_explicit_persist_flag;runtime_activation_requires_execution_shadow_cycle_selection;broker_order_construction_and_account_mutation_require_separate_execution_gate',
    applies_to = 'trading-execution;trading-manager;formal_realtime_integration;provider_observe;manager_persistence;runtime_activation_gate;broker_execution_gate',
    note = 'Formal realtime integration policy separating approved provider observation and explicit manager evidence persistence from later execution-owned runtime activation and broker/account mutation gates.',
    updated_at = NOW()
WHERE key = 'REALTIME_FORMAL_INTEGRATION_POLICY';
