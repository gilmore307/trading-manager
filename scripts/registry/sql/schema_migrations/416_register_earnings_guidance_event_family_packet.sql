-- Register earnings/guidance event-family scouting packet.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_EGFP001',
    'term',
    'EARNINGS_GUIDANCE_EVENT_FAMILY',
    'text',
    'earnings_guidance_event_family',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'event_family_scouting_packet_v1;event_interpretation_v1;event_activity_bridge;event_risk_governor',
    'sync_artifact',
    'Dedicated event family for scheduled earnings results, guidance updates, and narrative residuals linked to canonical earnings/report artifacts. Current status is scouting, not promotion evidence.'
  ),
  (
    'cfg_EGFP001',
    'config',
    'EARNINGS_GUIDANCE_CANONICAL_SOURCE_PRECEDENCE',
    'text',
    'sec_edgar_accepted_filing_or_company_exhibit;company_ir_release_or_transcript;nasdaq_earnings_calendar_shell;high_quality_news_narrative_residual;alpaca_or_gdelt_discovery_context;option_price_liquidity_activity_bridge_only',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'earnings_guidance_event_family;event_interpretation_v1;source_04_event_overlay;event_activity_bridge',
    'sync_artifact',
    'Canonical source precedence for earnings/guidance scouting. Calendar shells schedule events only; news is residual/discovery unless linked to official artifacts.'
  ),
  (
    'cfg_EGFP002',
    'config',
    'EARNINGS_GUIDANCE_REQUIRED_CLOCKS',
    'text',
    'event_awareness_time;scheduled_time;source_published_time;source_updated_time;available_time;interpretation_time;resolution_time;reaction_window',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'earnings_guidance_event_family;event_lifecycle_contract;event_interpretation_v1',
    'sync_artifact',
    'Required clocks for scheduled-known/outcome-later earnings events. Result facts are invalid before release artifact availability.'
  ),
  (
    'cfg_EGFP003',
    'config',
    'EARNINGS_GUIDANCE_REQUIRED_INTERPRETATION_FIELDS',
    'text',
    'event_phase;reported_period;release_phase;result_source_type;result_source_ref;eps_actual;eps_consensus;revenue_actual;revenue_consensus;eps_surprise_score;revenue_surprise_score;guidance_status;guidance_direction_score;guidance_magnitude_score;margin_quality_score;cash_flow_quality_score;capex_or_investment_intensity_score;balance_sheet_stress_score;management_tone_residual_score;narrative_residual_type;direction_bias_score;intensity_score;uncertainty_score;novelty_score;source_quality_score;evidence_confidence_score;review_status;standardization_status',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'earnings_guidance_event_family;event_interpretation_v1;event_family_scouting_packet_v1',
    'sync_artifact',
    'Minimum interpretation fields for the earnings/guidance family. Missing point-in-time values must remain missing or partial rather than inferred from later reaction.'
  ),
  (
    'cfg_EGFP004',
    'config',
    'EARNINGS_GUIDANCE_CONTROL_DESIGN',
    'text',
    'same_symbol_verified_non_earnings_windows;same_symbol_earnings_without_option_abnormality;prior_return_realized_volatility_liquidity_market_sector_price_controls;sector_bellwether_controls;release_phase_time_of_day_controls;verified_no_option_abnormality_controls',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'earnings_guidance_event_family;activity_price_relationship_study;event_activity_bridge;training_labels',
    'sync_artifact',
    'Required controls before earnings/guidance can move beyond scouting. Same-symbol price controls alone are insufficient when event/non-event status matters.'
  ),
  (
    'cfg_EGFP005',
    'config',
    'EARNINGS_GUIDANCE_MINIMUM_COVERAGE_GATE',
    'text',
    'canonical_event_shell_result_linkage;minimum_50_interpreted_windows_unless_explicitly_diagnostic;minimum_20_symbols;minimum_4_sectors_or_themes;multiple_earnings_seasons_or_diagnostic_label;verified_non_event_controls;explicit_missing_or_partial_fields;no_result_fields_before_release_visibility',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'earnings_guidance_event_family;event_family_scouting_packet_v1;model_promotion;event_risk_governor',
    'sync_artifact',
    'Minimum coverage gate before the earnings/guidance family may advance from scouting to pilot training.'
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
