-- Remove stale owner-approval wording from active promotion/storage/provider registry rows.

UPDATE trading_registry
SET payload = 'provider_allowlist_required;max_requests_required;max_window_required;dry_run_default;retry_after_respected;rate_limit_backoff_recorded;secret_values_never_logged;autonomous_historical_provider_acquisition_after_manager_controls',
    applies_to = 'trading-data;provider_calls;historical_provider_acquisition;control_plane;production_hardening',
    note = 'Provider/API access guardrails for automated historical acquisition: provider allowlists, request/window bounds, rate-limit backoff, retry discipline, resource controls, receipts, and failure registration. This is not a manual approval mechanism.',
    updated_at = NOW()
WHERE id = 'cfg_MSH008';

UPDATE trading_registry
SET applies_to = REPLACE(applies_to, 'owner_observed_agent_decision', 'agent_decision_evidence'),
    updated_at = NOW()
WHERE id IN ('scr_MODELPROMO002', 'scr_STORLIFE002', 'term_AGENTPROMO001', 'term_STORLIFE001');

UPDATE trading_registry
SET note = 'Historical provider acquisition may be dispatched and reconciled automatically while the owner observes and can intervene. Scope remains provider/data acquisition only; broker execution, model activation, promotion, and storage lifecycle mutation remain false unless their separate agent/policy gates pass.',
    updated_at = NOW()
WHERE id = 'trm_OWNEROBS001';
