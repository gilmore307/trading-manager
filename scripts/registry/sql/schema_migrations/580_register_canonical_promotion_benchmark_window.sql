-- Fix the ordinary promotion benchmark replay window for stable horizontal comparison.

UPDATE trading_registry
SET payload = 'candidate_policy_replay_benchmark;canonical_2021_2025_historical_clock_replay;model_selects_targets_from_candidate_policy;final_tickers_not_preselected;current_layer2_selected_watch_sectors;sector_constituents_or_reviewed_proxies;market_hot_liquid_names;liquidity_spread_data_quality_filters;optional_optionability_diagnostics;controls_for_contrast;fixed_replay_window_2021_01_01_to_2026_01_01_end_exclusive;fixed_data_snapshot;fixed_cost_model;fixed_baselines;fixed_guardrails;fixed_selection_metrics;training_flow_replay_forbidden;overlapping_training_folds_blocked;new_benchmark_requires_new_contract',
    note = 'Primary promotion benchmark policy. Target-selection models are judged by giving the candidate model the fixed historical-clock replay window 2021-01-01 through 2026-01-01 end-exclusive, covering the full 2021-2025 calendar years and 1255 expected NYSE trading days. The benchmark freezes the replay window, source snapshot, cost model, baseline ladder, guardrails, Layer 2 selected/watch sector inputs, sector constituent/proxy rules, market-wide hot/liquid-name admission rules, quality filters, optional optionability diagnostics, controls, and scoring metrics. The model must generate candidates, rank/select targets, run through the realtime decision route, and be judged by realized replay performance plus slice diagnostics. Fixed target/window panels and shared static benchmark-candidate CSVs are deleted and are not applicable to promotion benchmark judgment.',
    updated_at = NOW()
WHERE key = 'EVALUATION_PRIMARY_BENCHMARK_POLICY';

UPDATE trading_registry
SET payload = 'historical_clock_candidate_policy_replay_model_selects_targets_canonical_2021_2025',
    note = 'Promotion benchmark replay for target-selection models gives the candidate model the fixed historical-clock replay window 2021-01-01 through 2026-01-01 end-exclusive. It fixes candidate-generation policy, snapshot, costs, baselines, guardrails, and scoring metrics while requiring the model to select targets itself.',
    updated_at = NOW()
WHERE key = 'PROMOTION_BENCHMARK_CANDIDATE_POLICY_REPLAY';

UPDATE trading_registry
SET payload = 'canonical_2021_01_01_to_2026_01_01_end_exclusive_1255_expected_trading_days',
    note = 'Ordinary promotion benchmark contracts use the canonical fixed replay window 2021-01-01 through 2026-01-01 end-exclusive, covering the full 2021-2025 calendar years and 1255 expected NYSE trading days. Changing this window requires a new accepted benchmark contract decision.',
    updated_at = NOW()
WHERE key = 'PROMOTION_BENCHMARK_REPLAY_WINDOW_POLICY';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_EVALBMKCP001',
    'shared_artifact',
    'PROMOTION_BENCHMARK_CANDIDATE_POLICY_REPLAY_CONTRACT',
    'file',
    'trading-evaluation/benchmarks/promotion_benchmark_candidate_policy_replay.json',
    '/root/projects/trading-evaluation/benchmarks/promotion_benchmark_candidate_policy_replay.json',
    'trading-evaluation;promotion_eligibility;benchmark_contract;candidate_policy_replay',
    'sync_artifact',
    'Reviewable candidate-policy replay benchmark contract using the canonical 2021-2025 replay window. The contract fixes the window but remains pending frozen data snapshot and cost-model acceptance.'
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
