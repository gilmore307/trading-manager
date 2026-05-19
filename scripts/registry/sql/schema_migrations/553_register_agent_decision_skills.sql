-- Register fixed standards for every agent-owned decision surface.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_AGENTSKILL001',
    'config',
    'AGENT_DECISION_FIXED_SKILL_POLICY',
    'text',
    'all_agent_decisions_require_fixed_workspace_skill;model_comparisons_require_anonymous_labels;deterministic_callers_map_labels_after_review;defer_when_identity_blinding_fails',
    '/root/.openclaw/workspace/skills/openclaw',
    'script_called_agent_review;promotion_evaluation;runtime_model_lifecycle;target_context_review;server_error_diagnosis;storage_lifecycle;failure_register;event_strategy_promotion',
    'registry_only',
    'All agent decision surfaces must name a fixed workspace skill. Any model comparison shown to an agent must use anonymous labels and hide new/old/current/active/incumbent identity; deterministic caller code maps labels back after review.'
  ),
  (
    'cfg_EXECMLC002',
    'config',
    'RUNTIME_MODEL_LIFECYCLE_REVIEW_SKILL',
    'text',
    'runtime-model-lifecycle-review',
    '/root/.openclaw/workspace/skills/openclaw/runtime-model-lifecycle-review/SKILL.md',
    'trading-execution;runtime_model_lifecycle;shadow_cycle_selection;active_shadow_model_comparison;execution_active_model_config_write',
    'registry_only',
    'Workspace skill for execution-owned market-hours shadow-cycle roster review. It requires blinded model labels and returns active/realtime/shadow/eliminate recommendations without writing active pointers or mutating broker/account state.'
  ),
  (
    'cfg_TL2CTXREV002',
    'config',
    'TARGET_CONTEXT_REVIEW_SKILL',
    'text',
    'target-context-review',
    '/root/.openclaw/workspace/skills/openclaw/target-context-review/SKILL.md',
    'target_layer2_context_agent_review;target_layer2_context_mapping;proxy_review;optionability_gate',
    'registry_only',
    'Workspace skill for target-to-Layer-2 context review. It fixes the standard for reviewed context, target-specific proxies, optionability gates, and no Layer 1/2 universe mutation from the review.'
  ),
  (
    'cfg_AGENTERR005',
    'config',
    'SERVER_ERROR_DIAGNOSIS_SKILL',
    'text',
    'server-error-diagnosis',
    '/root/.openclaw/workspace/skills/openclaw/server-error-diagnosis/SKILL.md',
    'server_wide_agent_error_handoff;server_error_agent_request;agent_error_diagnosis;safe_repair',
    'registry_only',
    'Workspace skill for bounded server error diagnosis and safe internal repair. It forbids provider calls, broker/account mutation, secret disclosure, and durable data deletion without a separate gate.'
  ),
  (
    'cfg_STORLIFE004',
    'config',
    'STORAGE_LIFECYCLE_REVIEW_SKILL',
    'text',
    'storage-lifecycle-review',
    '/root/.openclaw/workspace/skills/openclaw/storage-lifecycle-review/SKILL.md',
    'agent_storage_lifecycle_decision;storage_lifecycle_request;backup;cleanup;archive;restore;delete',
    'registry_only',
    'Workspace skill for storage lifecycle review. It reviews backup/cleanup/archive/restore/delete evidence and explicitly forbids replacing accepted deletion with a trash-folder preservation workaround.'
  ),
  (
    'cfg_MGRFAILREV002',
    'config',
    'FAILURE_REGISTER_REVIEW_SKILL',
    'text',
    'failure-register-review',
    '/root/.openclaw/workspace/skills/openclaw/failure-register-review/SKILL.md',
    'failure_register;agent_review_required;retry_required;corrected;accepted_skip;unresolved',
    'registry_only',
    'Workspace skill for failure register disposition review. It fixes the standard for retry, corrected, accepted_skip, and unresolved decisions while preserving the original failure history.'
  ),
  (
    'cfg_EFRP002',
    'config',
    'EVENT_STRATEGY_PROMOTION_REVIEW_SKILL',
    'text',
    'event-strategy-promotion-review',
    '/root/.openclaw/workspace/skills/openclaw/event-strategy-promotion-review/SKILL.md',
    'event_family_strategy_promotion_review;event_failure_risk_model;layer_04_promotion;strategy_failure_label;event_interpretation',
    'registry_only',
    'Workspace skill for event-family and strategy-failure promotion review. It requires point-in-time interpretation, matched controls, leakage review, upstream non-overlap or residual value, and no trading action output.'
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

UPDATE trading_registry
SET payload = 'promotion-evaluation-review',
    note = 'Workspace skill that fixes the reviewer-agent standard for promotion eligibility: sealed benchmark integrity, hard guardrails, anonymous model comparison, uncertainty, and shadow readiness. Agent output is advisory only and does not activate models.',
    updated_at = NOW()
WHERE key = 'EVALUATION_PROMOTION_REVIEW_SKILL';

UPDATE trading_registry
SET payload = 'hard_guardrails;anonymous_model_vector_comparison;uncertainty_required;defer_when_not_materially_better;defer_when_identity_blinding_fails;agent_review_advisory_only',
    note = 'Promotion eligibility is judged by vector evidence, not a single score. Comparative model evidence must be blinded; if candidate superiority is unclear or identity blinding fails, the decision defers or requires shadow evidence rather than active selection.',
    updated_at = NOW()
WHERE key = 'EVALUATION_PROMOTION_VECTOR_RUBRIC_POLICY';

UPDATE trading_registry
SET payload = 'active_model_primary;promoted_not_active_shadow_during_market_hours;cycle_duration_about_one_month;anonymous_model_comparison_required;ranks_2_to_4_realtime_candidates;eliminate_requires_sufficient_reason;repeated_eliminate_can_retire;active_pointer_write_requires_separate_gate',
    note = 'Execution policy for runtime model lifecycle: active model remains trading authority, promoted candidates run shadow, mature cycle evidence is reviewed with anonymous model labels, and the active config pointer write requires a separate audited gate.',
    updated_at = NOW()
WHERE key = 'EXECUTION_RUNTIME_MODEL_LIFECYCLE_POLICY';

UPDATE trading_registry
SET payload = 'manager_schedules_evaluation_and_execution_reviews;fixed_agent_skills_required;anonymous_model_comparison_required;activation_owned_by_trading_execution',
    note = 'Agent promotion decisions may provide advisory evidence through fixed skills. Model comparisons must be anonymized. Offline promotion readiness is owned by trading-evaluation and runtime active model selection is owned by trading-execution.',
    updated_at = NOW()
WHERE key = 'MODEL_PROMOTION_SCRIPT_CALLED_AGENT_DECISION_POLICY';

UPDATE trading_registry
SET note = 'Manager-owned script-called agent review boundary for target-to-Layer-2 context mapping rows, target-specific auxiliary proxies, and multi-row equity business mappings. Reviewer agents must use the target-context-review skill.',
    updated_at = NOW()
WHERE key = 'TARGET_LAYER2_CONTEXT_AGENT_REVIEW';

UPDATE trading_registry
SET note = 'Request artifact containing selected target context mapping rows, required checks, forbidden actions, and the prompt for a reviewer agent using the target-context-review skill.',
    updated_at = NOW()
WHERE key = 'TARGET_LAYER2_CONTEXT_AGENT_REVIEW_REQUEST';

UPDATE trading_registry
SET note = 'Unified manager-owned handoff for server-side component errors that need agent diagnosis or safe repair. Reviewer agents must use the server-error-diagnosis skill; the handoff is not model-training-specific.',
    updated_at = NOW()
WHERE key = 'SERVER_WIDE_AGENT_ERROR_HANDOFF';

UPDATE trading_registry
SET note = 'Storage lifecycle policy/agent decision evidence for storage lifecycle mutation. Reviewer agents must use the storage-lifecycle-review skill; accepted deletion is deletion, not relocation to a trash-preservation folder.',
    updated_at = NOW()
WHERE key = 'AGENT_STORAGE_LIFECYCLE_DECISION';

UPDATE trading_registry
SET note = 'Every failed component request must be evaluated with the failure-register-review skill before manager can accept the failure as normal/expected and unlock downstream coverage. Accepted-failure coverage requires an agent review evidence reference and preserves failed_count separately from accepted_failed_count.',
    updated_at = NOW()
WHERE key = 'MANAGER_FAILED_REQUEST_AGENT_REVIEW_REQUIRED_POLICY';

UPDATE trading_registry
SET note = 'Promotion policy from Layer 9 EventRiskGovernor research into Layer 4 EventFailureRiskModel. Residual/event discovery may generate hypotheses and review packets, but event/strategy promotion requires the event-strategy-promotion-review skill and cannot automatically enter front decision scope.',
    updated_at = NOW()
WHERE key = 'EVENT_FAMILY_TO_LAYER_04_PROMOTION_POLICY';

