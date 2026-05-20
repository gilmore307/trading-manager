-- Refresh active current registry rows that still described the former nine-layer shape.

UPDATE trading_registry
SET payload = 'layer_01_proxy_gap_review_required;layer_10_event_adapter_review_required;layer_07_broker_account_route_deferred;layer_08_restriction_account_route_deferred;layer_09_thetadata_terminal_required',
    applies_to = 'trading-execution;realtime_input_coverage;layer_01_market_regime;layer_10_event_risk_governor;model_06_dynamic_risk_policy;model_06_position_projection;model_07_underlying_action;model_08_option_expression;model_09_event_risk_governor;current_physical_names',
    note = 'Current realtime coverage gap summary for the ten-layer stack. Layer 6 DynamicRiskPolicyModel is pending physical implementation, existing downstream physical surfaces retain model_06/model_07/model_08/model_09 tokens until renumbering, and Layer 10 event adapters remain bounded route gaps until reviewed implementation fills them.',
    updated_at = NOW()
WHERE key = 'EXECUTION_REALTIME_LAYER_GAP_SUMMARY';

UPDATE trading_registry
SET payload = 'physical_current_numbering_marked;historical_migrations_and_artifacts_unchanged;compatibility_aliases_only_for_prior_evidence_refs',
    applies_to = 'model_06_dynamic_risk_policy;model_06_position_projection;model_07_underlying_action;model_08_option_expression;model_09_event_risk_governor;source_09_event_risk_governor;feature_09_event_risk_governor;registry_current;openclaw_database',
    note = 'Audit follow-up after DynamicRiskPolicyModel insertion: active conceptual layers now use the ten-layer order, while downstream physical implementation names may retain prior model_06/model_07/model_08/model_09 tokens where explicitly marked until dedicated renumbering. Historical migrations and old artifacts are intentionally not rewritten.',
    updated_at = NOW()
WHERE key = 'LAYER_PHYSICAL_NUMBERING_AUDIT';

UPDATE trading_registry
SET note = 'Builds the accepted event-model acceptance report: EventRiskGovernor / EventIntelligenceOverlay is conceptual Layer 10 on the current stack while the physical model_09 package remains until renumbering; broad event alpha and signed earnings/guidance alpha remain blocked, diagnostic artifacts are preserved, and storage deletion stays on hold until reviewed regeneration completes.',
    updated_at = NOW()
WHERE key = 'MODEL_09_EVENT_RISK_GOVERNOR_ACCEPTANCE_REPORT_BUILD';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'layer_09_event_risk_governor', 'layer_10_event_risk_governor;model_09_event_risk_governor'),
    updated_at = NOW()
WHERE key = 'HISTORICAL_MODELING_SYSTEM_SERVICE_RUNTIME';
