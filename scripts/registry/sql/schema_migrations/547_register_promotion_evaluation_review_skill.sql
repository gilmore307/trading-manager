-- Register the fixed agent-review skill and once-only benchmark policy for evaluation promotion.

UPDATE trading_registry
SET payload = 'one_frozen_target_window;formal_run_once_after_training;benchmark_data_evaluation_only;long_complex_market_period;target_not_training_used;fixed_data_snapshot;fixed_cost_model;fixed_baselines;guardrails_do_not_replace_primary;new_benchmark_requires_new_contract',
    note = 'Primary evaluation benchmark policy. Fold-to-fold comparison uses one frozen target/window, formal benchmark execution happens once after training for a candidate lineage, and benchmark data is evaluation-only. Guardrails may block overfit but do not replace the primary benchmark without a new accepted contract.',
    updated_at = NOW()
WHERE key = 'EVALUATION_PRIMARY_BENCHMARK_POLICY';

UPDATE trading_registry
SET note = 'Evaluation-owned decision stating whether a model candidate is eligible for a later activation gate. It is based on frozen benchmark evidence and may use the fixed promotion-evaluation-review skill for advisory agent review; it is not production activation and has no broker/account side effects.',
    updated_at = NOW()
WHERE key = 'PROMOTION_ELIGIBILITY_DECISION';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_EVALPROMOREV001',
    'config',
    'EVALUATION_PROMOTION_REVIEW_SKILL',
    'text',
    'promotion-evaluation-review',
    '/root/.openclaw/workspace/skills/openclaw/promotion-evaluation-review/SKILL.md',
    'trading-evaluation;promotion_eligibility;fold_settlement;benchmark_overfit_control;script_called_agent_review',
    'registry_only',
    'Workspace skill that fixes the reviewer-agent standard for promotion eligibility: benchmark integrity, hard guardrails, incumbent vector comparison, uncertainty, shadow eligibility, and activation readiness. Agent output is advisory only.'
  ),
  (
    'cfg_EVALPROMOREV002',
    'config',
    'EVALUATION_PROMOTION_VECTOR_RUBRIC_POLICY',
    'text',
    'hard_guardrails;incumbent_vector_comparison;uncertainty_required;defer_when_not_materially_better;agent_review_advisory_only',
    'trading-evaluation/docs/40_promotion_eligibility.md;/root/.openclaw/workspace/skills/openclaw/promotion-evaluation-review/SKILL.md',
    'trading-evaluation;promotion_eligibility;model_promotion;benchmark_result;incumbent_comparison',
    'sync_artifact',
    'Promotion eligibility is judged by vector evidence, not a single score. If candidate superiority over the incumbent is unclear, the decision should defer or require shadow evidence rather than activate.'
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
