-- Reframe benchmark replay length from exact two-year to preferred five-year with a two-year minimum.

UPDATE trading_registry
SET payload = 'candidate_policy_replay_benchmark;preferred_five_year_historical_clock_replay;minimum_two_year_holdout;model_selects_targets_from_candidate_policy;final_tickers_not_preselected;current_layer2_selected_watch_sectors;sector_constituents_or_reviewed_proxies;market_hot_liquid_names;liquidity_spread_data_quality_filters;optional_optionability_diagnostics;controls_for_contrast;fixed_replay_window;fixed_data_snapshot;fixed_cost_model;fixed_baselines;fixed_guardrails;fixed_selection_metrics;training_flow_replay_forbidden;overlapping_training_folds_blocked;new_benchmark_requires_new_contract',
    note = 'Primary promotion benchmark policy. Target-selection models are judged by giving the candidate model a fixed historical-clock replay. About five years is preferred when data coverage is complete; two years is the minimum acceptable holdout. The benchmark freezes the replay window, source snapshot, cost model, baseline ladder, guardrails, Layer 2 selected/watch sector inputs, sector constituent/proxy rules, market-wide hot/liquid-name admission rules, quality filters, optional optionability diagnostics, controls, and scoring metrics. The model must generate candidates, rank/select targets, run through the realtime decision route, and be judged by realized replay performance plus slice diagnostics. Fixed target/window panels and shared static benchmark-candidate CSVs are deleted and are not applicable to promotion benchmark judgment.',
    updated_at = NOW()
WHERE key = 'EVALUATION_PRIMARY_BENCHMARK_POLICY';

UPDATE trading_registry
SET payload = 'historical_clock_candidate_policy_replay_model_selects_targets_preferred_five_year_minimum_two_year',
    note = 'Promotion benchmark replay for target-selection models gives the candidate model a fixed historical clock. About five years is preferred when coverage is complete; two years is the minimum acceptable holdout. It fixes candidate-generation policy, snapshot, costs, baselines, guardrails, and scoring metrics while requiring the model to select targets itself.',
    updated_at = NOW()
WHERE key = 'PROMOTION_BENCHMARK_CANDIDATE_POLICY_REPLAY';

DELETE FROM trading_registry
WHERE key = 'PROMOTION_BENCHMARK_TWO_YEAR_REPLAY_WINDOW';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'term_EVALBMKWIN001',
    'term',
    'PROMOTION_BENCHMARK_REPLAY_WINDOW_POLICY',
    'text',
    'preferred_five_year_replay_minimum_two_year_holdout',
    'trading-evaluation/docs/20_benchmark_contracts.md',
    'trading-evaluation;trading-model;trading-execution;promotion_eligibility;benchmark_contract',
    'sync_artifact',
    'Promotion benchmark contracts should give the candidate model about five years of historical-clock replay when coverage is complete. Two calendar years and 504 expected trading days are the minimum acceptable holdout, with final target selection performed by the model route rather than by a preselected ticker panel.'
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
