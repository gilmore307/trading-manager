-- Clarify that manager market-hours historical-work protection applies only on regular US equity trading days.

UPDATE trading_registry
SET payload = 'america_new_york_regular_equity_trading_day_protection;09:20-16:10_et_only_on_regular_us_equity_trading_days;pause_new_historical_provider_batches;pause_cpu_heavy_feature_model_eval;non_trading_days_do_not_trigger_time_window_pause;allow_light_bookkeeping_only;manual_override_requires_review',
    note = 'Default market-hours protection policy: during 09:20-16:10 ET on actual regular US equity trading days only, historical acquisition/modeling jobs pause or heavily throttle so live monitoring and execution retain priority. Weekends, NYSE holidays, and other non-trading days do not trigger the pause merely because the wall clock is inside that range.',
    updated_at = NOW()
WHERE id = 'cfg_MMHP001';
