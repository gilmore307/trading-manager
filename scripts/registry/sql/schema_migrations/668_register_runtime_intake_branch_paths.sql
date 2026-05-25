-- Register the accepted runtime graph shape: C01 splits the minute into
-- candidate-entry and open-position pools; C02 and C03 are sibling branches
-- that converge at C04 before C05/C06.

UPDATE trading_registry
SET payload = 'same_components_live_and_replay_different_adapters;evaluation_calls_execution_graph;numbered_runtime_component_catalog_c01_c07;c01_splits_candidate_entry_pool_and_open_position_pool;c02_entry_selection_from_candidate_pool;c03_open_position_lifecycle_branch;c04_converges_expression_review;c05_order_intent_sizing;c06_execution_gate;layer10_failure_explanation_only;separate_crypto_and_equity_options_accounts;no_cross_account_netting;fixed_crypto_pool_btc_eth_sol',
    note = 'Policy stating live trading and Replay use the same execution component graph and decision contracts, with only adapter profiles swapped. C01 Intake reads account state, current holdings, dynamic remaining sector opportunity mix, and accepted target candidates, then emits candidate_entry_pool for C02 Entry and open_position_pool for C03 Lifecycle. C02 and C03 are sibling branches that converge at C04 expression review before C05 order intent and C06 execution gate. trading-evaluation owns orchestration and judgment, not duplicated trading decisions. Runtime decisions must keep crypto and equity/options in independent account sleeves without cross-account collateral, buying-power, position, or risk-budget netting.',
    updated_at = NOW()
WHERE key = 'EXECUTION_RUNTIME_COMPONENT_GRAPH_POLICY';

UPDATE trading_registry
SET payload = 'C01 Intake=component_01_intake;candidate_entry_pool->C02 Entry=component_02_entry;open_position_pool->C03 Lifecycle=component_03_lifecycle;C02/C03 accepted intents->C04 Option Review=component_04_option_review;C05 Order Intent=component_05_order_intent;C06 Execution Gate=component_06_execution_gate;C07 Failure Review=component_07_failure_review',
    applies_to = 'trading-execution;runtime_component_graph;live;replay;component_catalog;execution_paths',
    note = 'Accepted concise numbered runtime component catalog and execution paths. C01 Intake is the split point: candidate_entry_pool routes to C02 Entry, while open_position_pool routes to C03 Lifecycle. C02 and C03 are sibling branches, not a linear dependency. Accepted C02/C03 underlying intents converge at C04 expression review before C05 order intent and C06 execution gate. C07 Failure Review is a post-failure branch only; it is not a normal pre-order step.',
    updated_at = NOW()
WHERE key = 'EXECUTION_RUNTIME_COMPONENT_SEQUENCE';

UPDATE trading_registry
SET payload = 'candidate_entry_pool;open_position_pool;watch_targets_compatibility_alias;open_position_refs_compatibility_summary;remaining_strong_sector_targets;recent_high_trading_volume_targets;recent_abnormal_volume_targets;recent_news_or_earnings_catalyst_targets;filled_sector_removes_sector_reason_only',
    applies_to = 'component_01_intake;execution_intake_snapshot;candidate_entry_pool;open_position_pool;blocked_targets;component_02_entry;component_03_lifecycle',
    note = 'C01 maintains the equity/options candidate_entry_pool as the union of remaining strong-sector targets, recent high-volume targets, recent abnormal-volume targets, and recent news or earnings catalyst targets. It also emits open_position_pool for already-open positions that bypass C02 and route directly to C03 Lifecycle. A filled sector removes only the strong-sector opportunity reason; targets from that sector can still enter through high-volume, abnormal-volume, or catalyst evidence. High-volume means a reviewed flag or volume/dollar-volume score or percentile >= 0.80. Abnormal-volume means a reviewed flag, relative/abnormal volume score >= 0.80, relative volume >= 2.0x, or volume z-score >= 2.0.',
    updated_at = NOW()
WHERE key = 'C01_CANDIDATE_POOL_POLICY';

UPDATE trading_registry
SET note = 'Execution runtime contract emitted by C01 Intake for account balance state, current holdings, dynamic remaining sector opportunity mix, accepted candidate-entry targets, and account-sleeve candidate filtering. It emits candidate_entry_pool for C02 Entry and open_position_pool for C03 Lifecycle; watch_targets and open_position_refs may remain compatibility summaries. A filled sector removes only the sector-opportunity reason; independent high-volume, abnormal-volume, news, or earnings catalyst evidence may still admit the target. C01 does not allocate risk budget, size positions, decide entries, manage exits, construct orders, or mutate broker/account state.',
    updated_at = NOW()
WHERE key = 'EXECUTION_INTAKE_SNAPSHOT';

UPDATE trading_registry
SET payload = 'consume_c01_candidate_entry_pool_only;underlying_entry_thesis_only;status_suitable_deferred_rejected;no_balance_check;no_option_expression;no_direct_order_intent;suitable_routes_to_c04',
    note = 'C02 Entry consumes C01 candidate_entry_pool targets and decides which candidates have a suitable underlying entry thesis. It emits suitable, deferred, or rejected with entry direction, entry zone, target/take-profit, model invalidation, hard stop, horizon, and suitability score. C02 does not discover targets from the whole market, does not check account balance, choose option versus stock expression, select contracts, size positions, build orders, or directly authorize C05 order intents; suitable entries route to C04 expression review.',
    updated_at = NOW()
WHERE key = 'C02_ENTRY_THESIS_POLICY';

UPDATE trading_registry
SET note = 'Execution runtime contract emitted by C02 Entry for C01 candidate_entry_pool targets only. C02 selects which current candidates have underlying entry-thesis suitability; it is not a whole-market target discovery component. Status is suitable, deferred, or rejected. A suitable thesis includes direction, entry zone, target or take-profit zone, model invalidation price, hard stop price, horizon when available, and suitability score. C02 does not call Layer 9 or Layer 10, does not choose option versus stock expression, does not check account balance, and does not directly authorize order intents.',
    updated_at = NOW()
WHERE key = 'ENTRY_DECISION';

UPDATE trading_registry
SET note = 'C03 Lifecycle manages C01 open_position_pool rows in underlying-thesis terms. It is a sibling branch to C02, not downstream of C02. It decides hold, add, reduce, stop, exit, or take-profit from model stops, thesis invalidation, alpha, event risk, dynamic policy, position projection, and underlying action. Option contracts are expression translation owned by C04. Fixed option mark-to-market loss percentages are not ordinary lifecycle stops. C03 does not run fee, PDT, day-trade, churn, option-contract-cost, final buying-power-capacity, or final sizing formulas; every non-hold action must carry explicit reason evidence. Add/reduce decisions may include risk-based tranche management and thesis-aware high-sell/low-buy exposure adjustment only when trained M07/M08 evidence supports them. Live submission requires C06 agent final review.',
    updated_at = NOW()
WHERE key = 'C03_LIFECYCLE_UNDERLYING_REVIEW_POLICY';
