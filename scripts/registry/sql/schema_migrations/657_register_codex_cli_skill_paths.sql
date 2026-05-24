-- Point fixed review skill registry rows at Codex CLI skill sources.

UPDATE trading_registry
SET path = '/root/.openclaw/workspace/skills/codex',
    applies_to = 'script_called_codex_cli_review;promotion_evaluation;runtime_model_lifecycle;target_context_review;server_error_diagnosis;storage_lifecycle;failure_register;event_strategy_promotion',
    note = 'All Codex CLI decision surfaces must name a fixed workspace skill. Any model comparison shown to Codex must use anonymous labels and hide new/old/current/active/incumbent identity; deterministic caller code maps labels back after review.',
    updated_at = NOW()
WHERE key = 'AGENT_DECISION_FIXED_SKILL_POLICY';

UPDATE trading_registry
SET path = '/root/.openclaw/workspace/skills/codex/promotion-evaluation-review/SKILL.md',
    applies_to = 'trading-evaluation;promotion_eligibility;fold_settlement;replay_overfit_control;script_called_codex_cli_review',
    note = 'Codex CLI skill that fixes the reviewer standard for promotion eligibility: sealed replay integrity, hard guardrails, anonymous model comparison, uncertainty, and shadow readiness. Codex output is advisory only and does not activate models.',
    updated_at = NOW()
WHERE key = 'EVALUATION_PROMOTION_REVIEW_SKILL';

UPDATE trading_registry
SET path = 'trading-evaluation/docs/40_promotion_eligibility.md;/root/.openclaw/workspace/skills/codex/promotion-evaluation-review/SKILL.md',
    applies_to = 'trading-evaluation;promotion_eligibility;model_promotion;replay_result;incumbent_comparison',
    note = 'Promotion eligibility is judged by vector evidence, not a single score. Comparative model evidence must be blinded after the first promoted baseline exists; first_model_bootstrap may create that initial baseline without activation. If candidate superiority is unclear or identity blinding fails for later candidates, the decision defers or requires shadow evidence rather than active selection.',
    updated_at = NOW()
WHERE key = 'EVALUATION_PROMOTION_VECTOR_RUBRIC_POLICY';

UPDATE trading_registry
SET path = '/root/.openclaw/workspace/skills/codex/event-strategy-promotion-review/SKILL.md',
    note = 'Codex CLI skill for event-family and strategy-failure promotion review. It requires point-in-time interpretation, matched controls, leakage review, upstream non-overlap or residual value, and no trading action output.',
    updated_at = NOW()
WHERE key = 'EVENT_STRATEGY_PROMOTION_REVIEW_SKILL';

UPDATE trading_registry
SET path = '/root/.openclaw/workspace/skills/codex/failure-register-review/SKILL.md',
    note = 'Codex CLI skill for failure register disposition review. It fixes the standard for retry, corrected, accepted_skip, and unresolved decisions while preserving the original failure history.',
    updated_at = NOW()
WHERE key = 'FAILURE_REGISTER_REVIEW_SKILL';

UPDATE trading_registry
SET path = '/root/.openclaw/workspace/skills/codex/runtime-model-lifecycle-review/SKILL.md',
    note = 'Codex CLI skill for execution-owned market-hours shadow-cycle roster review. It requires blinded model labels and returns active/realtime/shadow/eliminate recommendations without writing active pointers or mutating broker/account state.',
    updated_at = NOW()
WHERE key = 'RUNTIME_MODEL_LIFECYCLE_REVIEW_SKILL';

UPDATE trading_registry
SET path = '/root/.openclaw/workspace/skills/codex/server-error-diagnosis/SKILL.md',
    note = 'Codex CLI skill for bounded server error diagnosis and safe internal repair. It forbids broker/account mutation, secret disclosure, and durable data deletion without a separate gate.',
    updated_at = NOW()
WHERE key = 'SERVER_ERROR_DIAGNOSIS_SKILL';

UPDATE trading_registry
SET path = '/root/.openclaw/workspace/skills/codex/storage-lifecycle-review/SKILL.md',
    note = 'Codex CLI skill for storage lifecycle review. It reviews backup/cleanup/archive/restore/delete evidence and explicitly forbids replacing accepted deletion with a trash-folder preservation workaround.',
    updated_at = NOW()
WHERE key = 'STORAGE_LIFECYCLE_REVIEW_SKILL';

UPDATE trading_registry
SET path = '/root/.openclaw/workspace/skills/codex/target-context-review/SKILL.md',
    note = 'Codex CLI skill for target-to-Layer-2 context review. It fixes the standard for reviewed context, target-specific proxies, optionability gates, and no Layer 1/2 universe mutation from the review.',
    updated_at = NOW()
WHERE key = 'TARGET_CONTEXT_REVIEW_SKILL';
