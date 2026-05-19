-- Register benchmark panel target/window exclusion policy.

UPDATE trading_registry
SET payload = 'one_frozen_benchmark_panel;fixed_component_weights;formal_run_once_after_training;benchmark_data_evaluation_only;long_complex_market_period;target_window_training_exclusion_required;same_target_overlapping_folds_blocked;fixed_data_snapshot;fixed_cost_model;fixed_baselines;guardrails_do_not_replace_primary;new_benchmark_requires_new_contract',
    note = 'Primary evaluation benchmark policy. Fold-to-fold comparison uses one frozen panel with fixed target/window components and fixed weights. Formal benchmark execution happens once after training for a candidate lineage, benchmark data is evaluation-only, and any same-target training fold that overlaps a benchmark component window is blocked.',
    updated_at = NOW()
WHERE key = 'EVALUATION_PRIMARY_BENCHMARK_POLICY';

UPDATE trading_registry
SET note = 'Frozen primary benchmark panel contract for independent fold settlement. It fixes target/window components, component weights, data snapshot, cost model, baselines, guardrails, and same-target training-exclusion evidence.',
    updated_at = NOW()
WHERE key = 'EVALUATION_BENCHMARK_CONTRACT';

UPDATE trading_registry
SET note = 'Validation artifact for the frozen benchmark panel contract. It checks benchmark target/window overlap against training exclusions, component weights, market-condition coverage, baselines, cost model, and data snapshot evidence.',
    updated_at = NOW()
WHERE key = 'EVALUATION_BENCHMARK_CONTRACT_VALIDATION';

