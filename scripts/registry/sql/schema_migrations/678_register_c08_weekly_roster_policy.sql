-- Register accepted C08 weekly roster and probation-elimination policy.

UPDATE trading_registry
SET applies_to = 'trading-execution;runtime_model_lifecycle;active_model_selection;c08_weekly_roster;stable_wingmen;rotating_challengers;probation_wingman;eliminate_candidates',
    note = 'Execution-owned post-shadow-cycle model roster selection. It chooses one active model group, stable wingmen, a probation wingman when present, rotating challengers, shadow-only candidates, and eliminate candidates from mature market-hours evidence without broker/order/account mutation.',
    updated_at = NOW()
WHERE id = 'art_MPR002';

UPDATE trading_registry
SET applies_to = 'trading-execution;runtime_model_lifecycle;active_model_selection;c08_weekly_roster;stable_wingmen;rotating_challengers;probation_wingman;eliminate_candidates',
    note = 'Post-cycle execution roster decision: selected active model, stable wingmen, optional probation wingman, rotating challengers, shadow-only candidates, and eliminate candidates with reason evidence. No broker/order/account mutation is performed.',
    updated_at = NOW()
WHERE id = 'art_EXECMLC001';

UPDATE trading_registry
SET payload = 'active_model_primary;promoted_not_active_shadow_during_market_hours;weekly_rerank;one_active_three_stable_wingmen_two_rotating_challengers;probation_uses_one_stable_wingman_slot;probation_failed_expedited_elimination_review;anonymous_model_comparison_required;active_pointer_write_requires_separate_gate',
    applies_to = 'trading-execution;runtime_model_lifecycle;c08_weekly_roster;active_model_selection;runtime_promoted_eligibility',
    note = 'Execution policy for runtime model lifecycle: active model remains the only trading authority. C08 normally runs one active, three stable wingmen, and two rotating challengers. If one elimination-probation candidate needs final realtime review, it occupies one stable wingman slot for that weekly cycle. If evidence coverage is valid and the probation cycle remains weak, expedited elimination review can remove the model from runtime promoted eligibility. This is distinct from promotion Replay, which uses fixed historical data and must not call execution_shadow_cycle_selection.',
    updated_at = NOW()
WHERE id = 'cfg_EXECMLC001';

UPDATE trading_registry
SET payload = 'c08_model_group_shadow_comparison_intraday_component;realtime_data_only;already_promoted_model_groups_only;not_replay;active_model_only_trading_authority;capacity_gated;one_active_three_stable_wingmen_two_rotating_challengers;probation_uses_one_stable_wingman_slot',
    note = 'C08 Model Group Shadow Comparison is a market-hours realtime component for comparing the active model group with eligible already-promoted shadow model groups. Shadow outputs are evidence only; only the current active model can route decisions into live C01-C06 trading authority until an execution_active_model_config_write gate changes the pointer. C08 must be capacity-gated and normally admits one active, three stable wingmen, and two rotating challengers; one probation candidate may use a stable wingman slot for final realtime evidence.',
    updated_at = NOW()
WHERE id = 'cfg_SHADOWC08001';
