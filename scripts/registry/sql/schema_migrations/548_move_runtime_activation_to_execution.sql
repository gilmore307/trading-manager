-- Move final runtime activation/roster selection to trading-execution.

UPDATE trading_registry
SET payload = 'execution_shadow_cycle_selection',
    path = 'trading-execution/docs/40_runtime_model_lifecycle.md;trading-execution/src/trading_execution/model_lifecycle.py',
    applies_to = 'trading-execution;runtime_model_lifecycle;active_model_selection;shadow_candidates;eliminate_candidates',
    note = 'Execution-owned post-shadow-cycle model roster selection. It chooses active, realtime-candidate, shadow-only, and eliminate-candidate roles from mature market-hours evidence without broker/order/account mutation.',
    updated_at = NOW()
WHERE key = 'ACTIVATION_RECORD_ARTIFACT';

UPDATE trading_registry
SET key = 'EVALUATION_PROMOTION_READINESS_RECORD',
    payload = 'promotion_readiness_record',
    path = 'trading-evaluation/docs/50_promotion_readiness.md;trading-evaluation/src/trading_evaluation/activation.py',
    applies_to = 'trading-evaluation;promotion_readiness;execution_shadow_admission;rollback_ref',
    note = 'Evaluation-owned readiness record emitted after an eligible promotion_eligibility_decision. It admits a candidate to execution shadow review and does not switch active model configs.',
    updated_at = NOW()
WHERE key = 'EVALUATION_MODEL_ACTIVATION_RECORD';

UPDATE trading_registry
SET key = 'EXECUTION_ACTIVE_MODEL_CONFIG',
    path = 'trading-execution/docs/40_runtime_model_lifecycle.md',
    applies_to = 'trading-execution;runtime_model_lifecycle;active_model_config;realtime_consumption',
    note = 'Execution-owned active model config pointer after runtime shadow-cycle selection and a separate active-pointer write gate. Evaluation produces promotion readiness only.',
    updated_at = NOW()
WHERE key = 'EVALUATION_ACTIVE_MODEL_CONFIG';

UPDATE trading_registry
SET key = 'EVALUATION_PROMOTION_READINESS_POLICY',
    payload = 'evaluation_owns_offline_promotion_readiness;execution_owns_runtime_activation;eligible_decision_required;rollback_ref_required;broker_account_mutation_forbidden',
    path = 'trading-evaluation/docs/50_promotion_readiness.md;trading-execution/docs/40_runtime_model_lifecycle.md',
    applies_to = 'trading-evaluation;promotion_readiness;trading-execution;runtime_activation;trading-manager',
    note = 'Evaluation owns offline promotion readiness; execution owns live/shadow runtime activation selection. Manager schedules only, and broker/account mutation remains outside both records.',
    updated_at = NOW()
WHERE key = 'EVALUATION_PROMOTION_ACTIVATION_POLICY';

UPDATE trading_registry
SET key = 'TRADING_EVALUATION_BUILD_PROMOTION_READINESS_RECORD',
    payload = 'PYTHONPATH=src python3 scripts/evaluation/build_promotion_readiness_record.py --promotion-eligibility-json $PROMOTION_ELIGIBILITY_JSON --candidate-model-ref $CANDIDATE_MODEL_REF --candidate-config-ref $CANDIDATE_CONFIG_REF --rollback-ref $ROLLBACK_REF',
    path = '/root/projects/trading-evaluation/scripts/evaluation/build_promotion_readiness_record.py',
    applies_to = 'trading-evaluation;promotion_readiness_record;promotion_eligibility_decision;execution_shadow_admission',
    note = 'Build an evaluation-owned promotion_readiness_record from an eligible promotion_eligibility_decision. The script performs no provider calls, SQL mutation, storage lifecycle mutation, active model switch, broker execution, order construction, or account mutation.',
    updated_at = NOW()
WHERE key = 'TRADING_EVALUATION_BUILD_MODEL_ACTIVATION_RECORD';

UPDATE trading_registry
SET payload = 'manager_schedules_evaluation_and_execution_reviews;activation_owned_by_trading_execution',
    applies_to = 'model_promotion_review;advisory_evidence;trading-evaluation;trading-execution;runtime_activation',
    note = 'Agent promotion decisions may provide advisory evidence, but offline promotion readiness is owned by trading-evaluation and runtime active model selection is owned by trading-execution.',
    updated_at = NOW()
WHERE key = 'MODEL_PROMOTION_SCRIPT_CALLED_AGENT_DECISION_POLICY';

UPDATE trading_registry
SET payload = 'manager_promotion_request_not_activation;evaluation_owns_promotion_readiness;execution_owns_runtime_activation;broker_account_still_separate',
    path = 'trading-manager/docs/05_decision.md;trading-evaluation/docs/50_promotion_readiness.md;trading-execution/docs/40_runtime_model_lifecycle.md',
    applies_to = 'trading-manager;trading-evaluation;trading-execution;runtime_activation;broker_account_boundary;historical_scheduler',
    note = 'Manager promotion scheduling does not activate a live model, switch production pointers, submit orders, mutate accounts, or authorize live trading. Runtime active model selection is execution-owned and broker/account mutation remains separate.',
    updated_at = NOW()
WHERE key = 'PROMOTION_NOT_ACTIVATION_POLICY';

UPDATE trading_registry
SET payload = 'candidate_ref_required;evaluation_run_refs_optional;evidence_refs_optional;manager_schedules_only;evaluation_owns_benchmark_settlement_eligibility_readiness;execution_owns_shadow_cycle_activation',
    applies_to = 'model_promotion_review;trading-evaluation;fold_settlement;promotion_eligibility;promotion_readiness;trading-execution;runtime_activation',
    note = 'Manager prepares and schedules model promotion/evaluation/execution-review requests. Benchmark judgment and promotion readiness belong to trading-evaluation; live/shadow runtime active selection belongs to trading-execution.',
    updated_at = NOW()
WHERE key = 'MODEL_PROMOTION_UNIFIED_REVIEW_POLICY';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_EXECMLC001',
    'artifact_type',
    'EXECUTION_SHADOW_CYCLE_SELECTION',
    'text',
    'execution_shadow_cycle_selection',
    'trading-execution/docs/40_runtime_model_lifecycle.md;trading-execution/src/trading_execution/model_lifecycle.py',
    'trading-execution;runtime_model_lifecycle;active_model_selection;realtime_candidates;eliminate_candidates',
    'sync_artifact',
    'Post-cycle execution roster decision: selected active model, ranks 2-4 realtime candidates, shadow-only candidates, and eliminate candidates with reason evidence. No broker/order/account mutation is performed.'
  ),
  (
    'cfg_EXECMLC001',
    'config',
    'EXECUTION_RUNTIME_MODEL_LIFECYCLE_POLICY',
    'text',
    'active_model_primary;promoted_not_active_shadow_during_market_hours;cycle_duration_about_one_month;ranks_2_to_4_realtime_candidates;eliminate_requires_sufficient_reason;repeated_eliminate_can_retire',
    'trading-execution/docs/40_runtime_model_lifecycle.md',
    'trading-execution;runtime_model_lifecycle;shadow_monitoring;active_model_selection',
    'sync_artifact',
    'Execution policy for runtime activation: active model remains trading authority, promoted candidates run shadow, mature cycle evidence selects active/realtime/eliminate roles, and weak candidates retire only after sufficient repeated evidence.'
  ),
  (
    'scr_EXECMLC001',
    'script',
    'TRADING_EXECUTION_BUILD_SHADOW_CYCLE_SELECTION',
    'command',
    'PYTHONPATH=src python3 scripts/execution/build_shadow_cycle_selection.py --cycle-ref $CYCLE_REF --current-active-model-ref $CURRENT_ACTIVE_MODEL_REF --candidate-reviews-jsonl $CANDIDATE_REVIEWS_JSONL',
    '/root/projects/trading-execution/scripts/execution/build_shadow_cycle_selection.py',
    'trading-execution;execution_shadow_cycle_selection;runtime_model_lifecycle',
    'sync_artifact',
    'Build an execution_shadow_cycle_selection record from ranked market-hours active/shadow review rows. The script writes no active pointer, constructs no orders, calls no brokers, and mutates no accounts.'
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
