-- Register final event-layer judgment after canonical earnings/guidance scouting.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_ELFJ001',
    'term',
    'EVENT_LAYER_FINAL_JUDGMENT_20260515',
    'text',
    'event_layer_accepted_as_bounded_event_risk_governor_not_broad_event_alpha',
    'trading-model/docs/102_event_layer_final_judgment.md',
    'event_risk_governor;event_family_scouting;event_activity_bridge;model_promotion',
    'sync_artifact',
    'Final judgment after option abnormality, matched-control, raw-news, and canonical earnings/guidance scouting: keep/build EventRiskGovernor as bounded risk/intelligence overlay; do not promote broad event alpha, standalone option abnormality, or EventActivityBridgeModel.'
  ),
  (
    'cfg_ELFJ001',
    'config',
    'EVENT_RISK_GOVERNOR_CURRENT_BUILD_BOUNDARY',
    'text',
    'canonical_event_timeline;event_interpretation_when_reviewed;event_activity_bridge_as_provenance;uncertainty_review_block_cap_reduce_flatten_hints;no_broker_mutation;no_broad_event_alpha',
    'trading-model/docs/102_event_layer_final_judgment.md',
    'event_risk_governor;execution_boundary;model_promotion',
    'sync_artifact',
    'Machine-readable current build boundary for the event layer. It is a risk-governor/intelligence overlay, not an order engine or broad event-alpha layer.'
  ),
  (
    'trm_ELFJ002',
    'term',
    'EARNINGS_GUIDANCE_EVENT_FAMILY_STATUS_AFTER_CANONICAL_SCOUTING',
    'text',
    'scouting',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'earnings_guidance_event_family;event_family_scouting_packet_v1',
    'sync_artifact',
    'The canonical calendar shell/control pass supports continued scouting only; it is underpowered and lacks official result/guidance interpretation plus verified no-option-abnormality controls.'
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
