-- Move active legacy PDT/day-trade add feasibility into C03 early lifecycle checks.

UPDATE trading_registry
SET payload = 'underlying_first_lifecycle;options_are_expression_translation;model_underlying_stop_required;no_fixed_option_loss_stop;explicit_reason_evidence_required;respect_sector_opportunity_mix;legacy_pdt_day_trade_add_feasibility_under_25000;broker_pdt_framework_retired_disables_legacy_check;agent_final_review_before_live_submission',
    note = 'C03 Lifecycle manages already-open positions in underlying-thesis terms. It decides hold, add, reduce, stop, exit, or take-profit from model stops, thesis invalidation, alpha, event risk, dynamic policy, position projection, and underlying action. Option contracts are expression translation owned by C04. Fixed option mark-to-market loss percentages are not ordinary lifecycle stops. C03 does not run fee or churn formulas; every non-hold action must carry explicit reason evidence. Add decisions must respect C01/M07 sector-opportunity and portfolio constraints, and when the legacy broker PDT/day-trade framework is active with account equity below $25,000, C03 blocks non-critical adds that account context marks as day-trade unavailable. Broker context marking PDT retired, replaced, not applicable, or migrated to intraday margin disables this legacy add block. Live submission still requires C07 agent final review.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_EXECRTC006';

UPDATE trading_registry
SET payload = 'required_before_live_submission;applies_to_open_add_reduce_exit_stop_take_profit_roll_stock_fallback;review_reason_evidence;review_sector_mix_compliance;review_broker_regulatory_context;review_fees_spread_context;hard_broker_or_regulatory_blocks_reject',
    note = 'C07 Execution Gate requires an approved agent final review before any live broker submission for open, add, reduce, exit, stop, take-profit, option roll, or stock fallback orders. The review consumes C02/C03/C04 reason evidence, sector/opportunity-mix compliance, broker/regulatory context, fees, spread, and transaction costs. C03 pre-blocks legacy under-$25,000 PDT/day-trade add infeasibility when active; broker/regulatory hard blocks still reject outright.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_EXECRTC007';

UPDATE trading_registry
SET note = 'Execution runtime contract emitted by C03 Lifecycle for already-open position management. C03 is underlying-first: it decides hold, add, reduce, exit, stop, take-profit, or flatten-review from model-provided underlying thesis state, alpha, event risk, dynamic policy, and position projection. For the high-risk options account it does not use fixed option mark-to-market loss percentages as ordinary stops; C04 owns option expression translation. C03 emits explicit reason evidence, blocks add when C01/M07 sector-opportunity or portfolio constraints are already filled, and pre-blocks active legacy PDT/day-trade add infeasibility for under-$25,000 accounts until broker context marks the legacy framework retired or replaced.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'art_EXECRTC005';

UPDATE trading_registry
SET note = 'Accepted concise numbered intraday execution component sequence. C01 Intake owns account/watch-target intake; C02 Entry owns underlying entry-thesis suitability; C03 Lifecycle owns underlying-first open-position lifecycle with model stops, reason evidence, sector/opportunity add constraints, and active legacy under-$25,000 PDT/day-trade add feasibility; C04 owns option/underlying expression review; C07 owns the agent-reviewed live-submission gate. component_id values follow the model-aligned physical naming pattern component_01_* through component_07_*.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_EXECRTC003';
