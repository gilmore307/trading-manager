-- Disable market-hours historical-training backoff during pre-promotion full-training mode.

UPDATE trading_registry
SET payload = 'pre_promotion_full_training_mode;market_hours_historical_training_backoff_disabled_until_production_model_activation;resource_pressure_gate_still_active;provider_calls_still_require_live_call_approval_v1;model_activation_still_requires_approved_review_decision;broker_order_fill_account_mutation_still_blocked;reenable_market_hours_protection_before_live_trading',
    note = 'Current pre-promotion scheduler policy: no production model/live trading capacity is active yet, so regular-session market-hours backoff is disabled to prioritize first promotable-model evidence. Host resource gates, provider approval gates, promotion review gates, and broker/execution mutation gates remain hard. Re-enable market-hours protection before production model activation/live trading.',
    updated_at = NOW()
WHERE id = 'cfg_MMHP001';
