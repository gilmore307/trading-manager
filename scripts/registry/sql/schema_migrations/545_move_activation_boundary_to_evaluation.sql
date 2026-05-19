-- Move current model activation ownership to trading-evaluation.

UPDATE trading_registry
SET payload = 'model_activation_record',
    path = 'trading-evaluation/docs/50_activation.md;trading-evaluation/src/trading_evaluation/activation.py',
    applies_to = 'trading-evaluation;model_activation;active_model_config;rollback_ref;broker_account_forbidden',
    note = 'Evaluation-owned model activation record. It records active config release after an eligible promotion_eligibility_decision and rollback ref, while forbidding broker/order/account mutation.',
    updated_at = NOW()
WHERE key = 'ACTIVATION_RECORD_ARTIFACT';

UPDATE trading_registry
SET applies_to = 'review_decision;model_promotion_review;advisory_evidence;trading-manager',
    note = 'Generic manager advisory review decision artifact. It may inform evaluation, but it cannot activate configs; model activation belongs to trading-evaluation.',
    updated_at = NOW()
WHERE key = 'REVIEW_DECISION_ARTIFACT';

UPDATE trading_registry
SET payload = 'candidate_ref_required;evaluation_run_refs_optional;evidence_refs_optional;manager_schedules_only;evaluation_owns_benchmark_settlement_eligibility_activation',
    applies_to = 'model_promotion_review;trading-evaluation;fold_settlement;promotion_eligibility;model_activation',
    note = 'Manager prepares and schedules model promotion/evaluation requests. Benchmark judgment, promotion eligibility, active model config release, and model activation records belong to trading-evaluation.',
    updated_at = NOW()
WHERE key = 'MODEL_PROMOTION_UNIFIED_REVIEW_POLICY';

UPDATE trading_registry
SET applies_to = 'model_promotion_review;advisory_evidence;trading-manager;trading-evaluation',
    note = 'Manager-side helper for advisory review_decision artifacts only. It has no activation side effects; active model config release belongs to trading-evaluation.',
    updated_at = NOW()
WHERE key = 'MANAGER_REVIEW_DECISION_BUILD';

UPDATE trading_registry
SET applies_to = 'model_promotion_review;advisory_evidence;trading-manager;trading-evaluation',
    note = 'Script-called agent decision artifact retained as advisory evaluation evidence. It does not own activation; trading-evaluation owns promotion eligibility and model activation records.',
    updated_at = NOW()
WHERE key = 'AGENT_MODEL_PROMOTION_DECISION';

UPDATE trading_registry
SET payload = 'manager_agent_decision_advisory_only;activation_owned_by_trading_evaluation',
    applies_to = 'model_promotion_review;advisory_evidence;trading-evaluation;model_activation',
    note = 'Agent promotion decisions may provide advisory evidence, but production model activation is owned by trading-evaluation through promotion_eligibility_decision and model_activation_record.',
    updated_at = NOW()
WHERE key = 'MODEL_PROMOTION_SCRIPT_CALLED_AGENT_DECISION_POLICY';

UPDATE trading_registry
SET payload = 'manager_promotion_request_not_activation;activation_owned_by_trading_evaluation;broker_account_still_separate',
    path = 'trading-manager/docs/05_decision.md;trading-evaluation/docs/50_activation.md',
    applies_to = 'trading-manager;trading-evaluation;model_activation;broker_account_boundary;historical_scheduler',
    note = 'Manager promotion scheduling does not activate a live model, switch production pointers, submit orders, mutate accounts, or authorize live trading. Model activation records are evaluation-owned config-release artifacts; broker/account mutation remains separate.',
    updated_at = NOW()
WHERE key = 'PROMOTION_NOT_ACTIVATION_POLICY';

UPDATE trading_registry
SET applies_to = 'manager_request;model_promotion;trading-evaluation;fold_settlement;promotion_eligibility;model_activation',
    note = 'Single manager-side request type for scheduling evaluation-owned promotion work across every model layer. trading-evaluation owns benchmark settlement, promotion eligibility, and model activation records.',
    updated_at = NOW()
WHERE key = 'MODEL_PROMOTION_REVIEW';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_EVALACT001',
    'artifact_type',
    'EVALUATION_MODEL_ACTIVATION_RECORD',
    'text',
    'model_activation_record',
    'trading-evaluation/docs/50_activation.md;trading-evaluation/src/trading_evaluation/activation.py',
    'trading-evaluation;model_activation;active_model_config;rollback_ref',
    'sync_artifact',
    'Evaluation-owned model activation record emitted after an eligible promotion_eligibility_decision. It publishes config refs and rollback refs only; no broker/order/account mutation is allowed.'
  ),
  (
    'art_EVALACT002',
    'artifact_type',
    'EVALUATION_ACTIVE_MODEL_CONFIG',
    'text',
    'active_model_config',
    'trading-evaluation/docs/50_activation.md',
    'trading-evaluation;model_activation;active_model_config;realtime_consumption',
    'sync_artifact',
    'Evaluation-owned active model config pointer consumed by realtime/paper/live paths after activation. Execution consumes this config but does not decide activation.'
  ),
  (
    'cfg_EVALACT001',
    'config',
    'EVALUATION_PROMOTION_ACTIVATION_POLICY',
    'text',
    'evaluation_owns_model_activation;manager_schedules_only;eligible_decision_required;rollback_ref_required;active_model_config_ref_required;broker_account_mutation_forbidden',
    'trading-evaluation/docs/50_activation.md',
    'trading-evaluation;model_activation;promotion_eligibility;active_model_config;trading-manager',
    'sync_artifact',
    'Activation policy after boundary correction: trading-evaluation owns model activation records and active model config refs; manager schedules only; broker/account mutation remains outside activation.'
  ),
  (
    'scr_EVALACT001',
    'script',
    'TRADING_EVALUATION_BUILD_MODEL_ACTIVATION_RECORD',
    'command',
    'PYTHONPATH=src python3 scripts/evaluation/build_model_activation_record.py --promotion-eligibility-json $PROMOTION_ELIGIBILITY_JSON --activated-model-id $MODEL_ID --activated-config-ref $CONFIG_REF --active-model-config-ref $ACTIVE_CONFIG_REF --rollback-ref $ROLLBACK_REF --activation-scope $ACTIVATION_SCOPE',
    '/root/projects/trading-evaluation/scripts/evaluation/build_model_activation_record.py',
    'trading-evaluation;model_activation_record;promotion_eligibility_decision;active_model_config',
    'sync_artifact',
    'Build an evaluation-owned model_activation_record from an eligible promotion_eligibility_decision. The script performs no provider calls, SQL mutation, storage lifecycle mutation, broker execution, order construction, or account mutation.'
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
