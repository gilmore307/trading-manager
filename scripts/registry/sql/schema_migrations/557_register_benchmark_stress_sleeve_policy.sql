-- Register controlled benchmark stress-sleeve rules for data-edge cases.

UPDATE trading_registry
SET payload = 'one_frozen_benchmark_episode_panel;fixed_component_weights;asset_class_and_theme_bucket_required;component_role_required;hot_thematic_single_name_coverage_required;crypto_minority_sleeve_required;controlled_data_stress_sleeve_allowed;critical_data_stress_tags_require_stress_role;quote_only_crypto_component_allowed;missing_layer2_stress_component_allowed;stress_exception_ref_required;stress_sleeve_weight_cap_15_percent;non_etf_targets_require_target_context_review;formal_run_once_after_training;benchmark_data_evaluation_only;target_window_training_exclusion_required;same_target_overlapping_folds_blocked;fixed_data_snapshot;fixed_cost_model;fixed_baselines;guardrails_do_not_replace_primary;new_benchmark_requires_new_contract',
    note = 'Primary evaluation benchmark policy. Fold-to-fold comparison uses one frozen episode panel with fixed target/window components, asset-class and theme-bucket metadata, component roles, controlled hot thematic single-name coverage, a small crypto sleeve, and fixed weights. A capped stress sleeve may model critical data-edge cases such as quote-only crypto or missing Layer 2 context only with explicit stress role, data-availability tags, and stress-exception refs. Non-ETF targets require reviewed target-context/proxy refs unless an accepted stress exception applies. Benchmark data is evaluation-only and any same-target training fold that overlaps a benchmark component window is blocked.',
    updated_at = NOW()
WHERE key = 'EVALUATION_PRIMARY_BENCHMARK_POLICY';

UPDATE trading_registry
SET note = 'Frozen primary benchmark episode panel contract for independent fold settlement. It fixes target/window components, asset classes, theme buckets, component roles, component weights, data-availability tags, stress-exception refs for controlled data-edge cases, data snapshot, cost model, baselines, guardrails, target-context refs for non-ETF targets, and same-target training-exclusion evidence.',
    updated_at = NOW()
WHERE key = 'EVALUATION_BENCHMARK_CONTRACT';

UPDATE trading_registry
SET note = 'Validation artifact for the frozen benchmark episode panel contract. It checks benchmark target/window overlap against training exclusions, component weights, asset-class/theme metadata, component roles, stress-sleeve cap and exception refs, non-ETF target-context refs, market-condition coverage, baselines, cost model, and data snapshot evidence.',
    updated_at = NOW()
WHERE key = 'EVALUATION_BENCHMARK_CONTRACT_VALIDATION';
