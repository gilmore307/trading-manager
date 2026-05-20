-- Register reusable benchmark data snapshot and realtime replay boundary.

UPDATE trading_registry
SET payload = 'one_frozen_benchmark_episode_panel;fixed_component_weights;balanced_time_bucket_panel;recent_completed_windows_required;sector_coverage_required;consumer_coverage_required;entertainment_media_coverage_required;earnings_crossing_coverage_required;event_driven_coverage_required;asset_class_and_theme_bucket_required;component_role_required;single_name_optionable_majority_required;etf_backbone_minor_context_only;large_same_background_overlap_restrained;hot_thematic_single_name_coverage_required;crypto_minority_sleeve_required;controlled_data_stress_sleeve_allowed;critical_data_stress_tags_require_stress_role;missing_crypto_quote_order_book_context_allowed;missing_layer2_stress_component_allowed;stress_exception_ref_required;stress_sleeve_weight_cap_15_percent;non_etf_targets_require_target_context_review;formal_run_once_after_training;benchmark_data_evaluation_only;target_window_training_exclusion_required;same_target_overlapping_folds_blocked;one_time_data_construction;frozen_reusable_data_snapshot;candidate_specific_data_rebuild_forbidden;historical_clock_realtime_execution_replay;training_flow_replay_forbidden;fixed_data_snapshot;fixed_cost_model;fixed_baselines;guardrails_do_not_replace_primary;new_benchmark_requires_new_contract',
    note = 'Primary evaluation benchmark policy. Fold-to-fold comparison uses one frozen episode panel with fixed target/window components, balanced time-bucket weights across older and recent completed windows, explicit sector coverage including consumer and entertainment/media, explicit earnings-crossing and event-driven coverage, asset-class and theme-bucket metadata, component roles, a stock-first optionable single-name majority, restrained same-background event overlap, controlled hot thematic single-name coverage, a minor ETF background sleeve, a small crypto sleeve, and fixed weights. Benchmark data acquisition, event evidence collection, and source normalization are one-time construction phases that produce a frozen reusable data snapshot for the contract. All benchmark replay, fold settlement, promotion eligibility, guardrail, and regression checks reuse that snapshot; candidate-specific data rebuilds are forbidden. Benchmark replay uses the realtime execution decision route under a historical clock, not the model training pipeline. Event-driven coverage includes earnings, product-cycle repricing, policy/macro shocks, liquidity or squeeze events, data stress, and crypto-cycle regimes. Sector coverage includes consumer, entertainment/media, travel/leisure, retail, restaurants, healthcare, financials, energy, clean energy, nuclear/power, rare earth, AI compute, storage, optical networking, data-center infrastructure, and crypto. A capped stress sleeve may model critical data-edge cases such as crypto missing quote/order-book context or missing Layer 2 context only with explicit stress role, data-availability tags, and stress-exception refs. OKX crypto trades are transient inputs for trade-derived liquidity bars, not default standalone final saved outputs. Non-ETF targets require reviewed target-context/proxy refs unless an accepted stress exception applies. Benchmark data is evaluation-only and any same-target training fold that overlaps a benchmark component window is blocked.',
    updated_at = NOW()
WHERE key = 'EVALUATION_PRIMARY_BENCHMARK_POLICY';

UPDATE trading_registry
SET note = 'Storage runtime manifest describing component count, feed acquisition count, available/deferred/missing local coverage scan counts, acquisition-plan ref, frozen reusable snapshot ref once accepted coverage passes, and safety flags for a benchmark dataset preparation bundle. It records manager_request_route_used=false because benchmark data acquisition is a sealed one-shot action rather than a manager task route. The accepted snapshot is reused by every benchmark replay, settlement, promotion eligibility, guardrail, and regression check for the contract.',
    updated_at = NOW()
WHERE key = 'BENCHMARK_DATASET_PREPARATION_MANIFEST';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'term_EVALBMKRT001',
    'term',
    'BENCHMARK_REUSABLE_DATA_SNAPSHOT_POLICY',
    'text',
    'one_time_acquisition_then_frozen_reuse',
    'trading-evaluation/docs/22_benchmark_dataset_preparation.md',
    'trading-evaluation;benchmark_dataset_preparation;benchmark_replay;trading-storage',
    'sync_artifact',
    'Benchmark acquisition, event evidence collection, and source normalization are one-time construction phases. Once accepted, the frozen benchmark data snapshot is reused for benchmark replay, fold settlement, promotion eligibility, guardrails, and regression checks. Candidate-specific benchmark data rebuilds are forbidden.'
  ),
  (
    'term_EVALBMKRT002',
    'term',
    'BENCHMARK_REALTIME_REPLAY_ROUTE_POLICY',
    'text',
    'historical_clock_realtime_execution_replay_not_training_flow',
    'trading-evaluation/docs/22_benchmark_dataset_preparation.md',
    'trading-evaluation;trading-execution;benchmark_replay;promotion_eligibility',
    'sync_artifact',
    'Benchmark evaluation runs candidates through the realtime execution decision path under a historical clock and must not use the model training pipeline as the replay route. Replay consumes the frozen benchmark snapshot and triggers option-chain snapshots only from point-in-time model buy or option-expression decisions.'
  )
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();
