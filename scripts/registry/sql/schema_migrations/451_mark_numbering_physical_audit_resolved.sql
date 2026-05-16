-- Mark the active physical numbering audit as resolved for current-version tables/code.
-- Historical migration records and old artifacts intentionally remain unchanged.

UPDATE trading_registry
SET payload = 'physical_current_numbering_aligned;historical_migrations_and_artifacts_unchanged;compatibility_aliases_only_for_prior_evidence_refs',
    applies_to = 'model_08_event_risk_governor;model_04_alpha_confidence;model_05_position_projection;model_06_underlying_action;model_07_option_expression;source_08_event_risk_governor;feature_08_event_risk_governor;registry_current;openclaw_database',
    note = 'Audit follow-up resolved current-version physical numbering: live/current PostgreSQL table names, stored layer/model values, current registry rows, and current code defaults now follow the accepted conceptual order. Historical migrations and old artifacts are intentionally not rewritten.',
    updated_at = NOW()
WHERE key = 'LAYER_PHYSICAL_NUMBERING_AUDIT';
