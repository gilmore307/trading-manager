-- Align C07 with the accepted missed-event final review boundary.

UPDATE trading_registry
SET payload = 'required_before_live_submission;applies_to_open_add_reduce_exit_stop_take_profit_roll_stock_fallback;missed_event_guard;review_event_search_coverage;review_unconsumed_target_sector_macro_option_events;hard_broker_or_regulatory_blocks_reject',
    note = 'C07 Execution Gate requires an approved Codex CLI final review before any live broker submission for open, add, reduce, exit, stop, take-profit, option roll, or stock fallback orders. The review is a missed-event guard: it checks whether current target, sector, macro, regulatory, filing, analyst, halt, earnings, or option-market events are absent from upstream C02/C03/C04/M10 evidence. It does not re-run ordinary sizing, fee, spread, churn, or technical-thesis calculations. Broker/regulatory hard blocks still reject outright.',
    updated_at = NOW()
WHERE key = 'EXECUTION_AGENT_FINAL_REVIEW_POLICY';
