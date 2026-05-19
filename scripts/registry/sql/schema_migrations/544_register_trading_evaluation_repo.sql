-- Register the independent trading-evaluation repository and first evaluation contracts.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'rep_EVAL7K2Q',
    'repo',
    'TRADING_EVALUATION_REPO',
    'repo_name',
    'trading-evaluation',
    '/root/projects/trading-evaluation',
    'docs/01_context.md#component-repositories',
    'registry_only',
    'Canonical repository entry for the independent benchmark, fold-settlement, and promotion-eligibility component; remote: https://github.com/gilmore307/trading-evaluation.git'
  ),
  (
    'art_EVALBENCH001',
    'artifact_type',
    'EVALUATION_BENCHMARK_CONTRACT',
    'text',
    'evaluation_benchmark_contract',
    'trading-evaluation/docs/20_benchmark_contracts.md;trading-evaluation/src/trading_evaluation/benchmark.py',
    'trading-evaluation;benchmark_contract;fold_settlement;promotion_eligibility',
    'sync_artifact',
    'Frozen primary benchmark contract for independent fold settlement. It fixes one target/window plus data snapshot, cost model, baselines, guardrails, and training-exclusion evidence.'
  ),
  (
    'art_EVALBENCH002',
    'artifact_type',
    'EVALUATION_BENCHMARK_CONTRACT_VALIDATION',
    'text',
    'evaluation_benchmark_contract_validation',
    'trading-evaluation/src/trading_evaluation/benchmark.py;trading-evaluation/scripts/evaluation/validate_benchmark_contract.py',
    'trading-evaluation;benchmark_contract;validation',
    'sync_artifact',
    'Validation result for a benchmark contract. It blocks empty targets, short/simple windows, missing baselines, missing refs, and benchmark target overlap with training-used symbols.'
  ),
  (
    'art_EVALSETTLE001',
    'artifact_type',
    'FOLD_SETTLEMENT_RUN',
    'text',
    'fold_settlement_run',
    'trading-evaluation/docs/30_fold_settlement.md',
    'trading-evaluation;fold_settlement;model_evaluation;promotion_eligibility',
    'sync_artifact',
    'Future evaluation-owned settlement run over one completed fold and one accepted benchmark contract. Detailed reports are storage-owned artifacts by reference.'
  ),
  (
    'art_EVALSETTLE002',
    'artifact_type',
    'FOLD_SETTLEMENT_METRIC',
    'text',
    'fold_settlement_metric',
    'trading-evaluation/docs/30_fold_settlement.md',
    'trading-evaluation;fold_settlement;metric;model_evaluation',
    'sync_artifact',
    'Metric row emitted by fold settlement for returns, drawdown, risk-adjusted performance, turnover, abstention quality, event-risk intervention effect, calibration, and baseline comparisons.'
  ),
  (
    'art_EVALPROMO001',
    'artifact_type',
    'PROMOTION_ELIGIBILITY_DECISION',
    'text',
    'promotion_eligibility_decision',
    'trading-evaluation/docs/40_promotion_eligibility.md',
    'trading-evaluation;promotion_eligibility;model_promotion;activation_gate',
    'sync_artifact',
    'Evaluation-owned decision stating whether a model candidate is eligible for a later activation gate. It is not production activation and has no broker/account side effects.'
  ),
  (
    'cfg_EVALBENCH001',
    'config',
    'EVALUATION_PRIMARY_BENCHMARK_POLICY',
    'text',
    'one_frozen_target_window;long_complex_market_period;target_not_training_used;fixed_data_snapshot;fixed_cost_model;fixed_baselines;guardrails_do_not_replace_primary;new_benchmark_requires_new_contract',
    'trading-evaluation/docs/20_benchmark_contracts.md',
    'trading-evaluation;benchmark_contract;promotion_eligibility;horizontal_comparison',
    'sync_artifact',
    'Primary evaluation benchmark policy. Fold-to-fold comparison uses one frozen target/window; guardrails may block overfit but do not replace the primary benchmark without a new accepted contract.'
  ),
  (
    'scr_EVALBENCH001',
    'script',
    'TRADING_EVALUATION_VALIDATE_BENCHMARK_CONTRACT',
    'command',
    'PYTHONPATH=src python3 scripts/evaluation/validate_benchmark_contract.py --input $BENCHMARK_CONTRACT_JSON',
    '/root/projects/trading-evaluation/scripts/evaluation/validate_benchmark_contract.py',
    'trading-evaluation;evaluation_benchmark_contract;evaluation_benchmark_contract_validation',
    'sync_artifact',
    'Validate an evaluation benchmark contract JSON file. The validator has no provider calls, SQL mutation, storage lifecycle mutation, model activation, broker execution, or account mutation.'
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
