-- Register event-family scouting gate after option/news amplifier diagnostics.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_EFSC001',
    'term',
    'EVENT_FAMILY_SCOUTING_PACKET',
    'text',
    'event_family_scouting_packet_v1',
    'trading-model/docs/100_event_family_scouting.md',
    'event_interpretation_v1;event_activity_bridge;event_risk_governor;model_promotion',
    'sync_artifact',
    'Reviewed packet required before an event family enters model training, event-risk intervention promotion, or EventActivityBridgeModel promotion work.'
  ),
  (
    'cfg_EFSC001',
    'config',
    'EVENT_FAMILY_SCOUTING_PACKET_REQUIRED_FIELDS',
    'text',
    'event_family_key;family_status;family_definition;inclusion_criteria;exclusion_criteria;canonical_source_precedence;lifecycle_class_default;required_event_clocks;required_interpretation_fields;materiality_rules;surprise_or_known_status_rules;scope_routing_defaults;narrative_residual_rules;abnormal_activity_bridge_rules;control_design;forward_label_design;minimum_coverage_gate;early_stop_criteria;review_required_triggers;accepted_examples;near_miss_examples;negative_examples;source_artifact_refs;study_artifact_refs',
    'trading-model/docs/100_event_family_scouting.md',
    'event_family_scouting_packet_v1;event_interpretation_v1;event_activity_bridge;event_risk_governor',
    'sync_artifact',
    'Required fields for event-family scouting packets. Raw news proximity alone is not a valid family definition.'
  ),
  (
    'cfg_EFSC002',
    'config',
    'EVENT_FAMILY_ACCEPTANCE_STATUS_VALUES',
    'text',
    'proposed;scouting;pilot_training;accepted_active;deferred_low_signal;retired_no_signal;review_required',
    'trading-model/docs/100_event_family_scouting.md',
    'event_family_scouting_packet_v1;event_family_training;event_risk_governor;model_promotion',
    'sync_artifact',
    'Accepted event-family scouting status values. Deferred/retired families preserve evidence but must not advance to promotion work.'
  ),
  (
    'cfg_EFSC003',
    'config',
    'OPTION_ABNORMALITY_EVENT_RISK_AMPLIFIER_GATE',
    'text',
    'raw_option_abnormality_and_raw_news_proximity_not_sufficient;requires_event_interpretation_v1_family_materiality_lifecycle_controls',
    'trading-model/docs/100_event_family_scouting.md',
    'option_derivatives_abnormality;event_activity_bridge;event_risk_governor;activity_price_relationship_study',
    'sync_artifact',
    'Promotion gate from 2026-05-15 diagnostics: option abnormality may be reconsidered as an event-risk amplifier only through reviewed event-family interpretation, not raw news proximity.'
  ),
  (
    'cfg_EFSC004',
    'config',
    'EVENT_FAMILY_SCOUTING_INITIAL_STATUS',
    'text',
    'standalone_option_abnormality=deferred_low_signal;strict_option_abnormality_refinement=deferred_low_signal;raw_news_proximate_option_abnormality=deferred_low_signal;earnings_guidance_event_family=scouting',
    'trading-model/docs/100_event_family_scouting.md',
    'event_family_scouting_packet_v1;event_risk_governor;event_activity_bridge;option_activity',
    'sync_artifact',
    'Initial family statuses from option abnormality matched controls, strict-filter diagnostics, and Alpaca-news proximity amplifier slice.'
  ),
  (
    'cfg_EFSC005',
    'config',
    'EARNINGS_GUIDANCE_EVENT_FAMILY_SCOUTING_REQUIREMENTS',
    'text',
    'canonical_earnings_calendar_or_report_source;scheduled_known_outcome_later_lifecycle_split;no_result_fields_before_release_visibility;surprise_or_magnitude_fields_when_pit_available;option_bridge_relation_type;verified_non_event_and_non_earnings_controls;date_expiry_symbol_split_stability',
    'trading-model/docs/100_event_family_scouting.md',
    'earnings_guidance_event_family;event_family_scouting_packet_v1;event_interpretation_v1;event_activity_bridge',
    'sync_artifact',
    'Minimum requirements before the promising earnings/guidance option-amplifier slice may move beyond scouting.'
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
