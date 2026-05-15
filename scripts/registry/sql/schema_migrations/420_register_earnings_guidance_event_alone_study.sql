-- Register itemized earnings/guidance event-alone scouting study.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_EGEA001',
    'script',
    'MODEL_EARNINGS_GUIDANCE_EVENT_ALONE_STUDY',
    'text',
    'PYTHONPATH=src python3 scripts/models/model_04_event_overlay/run_earnings_guidance_event_alone_study.py',
    'trading-model/scripts/models/model_04_event_overlay/run_earnings_guidance_event_alone_study.py',
    'earnings_guidance_event_family;event_family_scouting_packet_v1;activity_price_relationship_study;event_risk_governor',
    'sync_artifact',
    'Deterministic local study entrypoint that tests canonical Nasdaq earnings-calendar shells against same-symbol non-earnings controls using daily equity bars. The study itself performs no provider calls.'
  ),
  (
    'trm_EGEA001',
    'term',
    'EARNINGS_GUIDANCE_EVENT_ALONE_Q4_2025_SCOUTING_STUDY',
    'text',
    'earnings_guidance_event_alone_scouting_study_v1',
    'trading-model/storage/earnings_guidance_event_alone_q4_2025_20260515',
    'earnings_guidance_event_family;event_family_scouting_packet_v1;activity_price_relationship_study;event_risk_governor',
    'sync_artifact',
    'First itemized earnings/guidance event-alone scout: 12 Q4 2025 earnings-shell events, 36 same-symbol non-earnings controls, positive direction-neutral path expansion, and weak/negative directional evidence. Diagnostic only; family remains scouting.'
  ),
  (
    'cfg_EGEA001',
    'config',
    'EARNINGS_GUIDANCE_NEXT_SCOUTING_STEP_AFTER_EVENT_ALONE',
    'text',
    'add_official_result_guidance_interpretation_then_compare_earnings_with_option_abnormality_vs_earnings_without_option_abnormality',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'earnings_guidance_event_family;event_family_scouting_packet_v1;model_promotion',
    'sync_artifact',
    'Next accepted route after event-alone scheduled-shell scout. Do not promote from scheduled shells alone; add official result/guidance interpretation and verified option-abnormality controls first.'
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
