-- Register earnings/guidance official-text candidate scout.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_EGTCS001',
    'script',
    'MODEL_EARNINGS_GUIDANCE_TEXT_CANDIDATE_SCOUT',
    'text',
    'PYTHONPATH=src python3 scripts/models/model_04_event_overlay/run_earnings_guidance_text_candidate_scout.py',
    'trading-model/scripts/models/model_04_event_overlay/run_earnings_guidance_text_candidate_scout.py',
    'earnings_guidance_event_family;event_family_scouting_packet_v1;event_risk_governor;model_promotion',
    'sync_artifact',
    'Deterministic local scout that extracts guidance/outlook-like candidate spans from acquired official document text; candidates remain review-required and perform no provider calls.'
  ),
  (
    'trm_EGTCS001',
    'term',
    'EARNINGS_GUIDANCE_TEXT_CANDIDATE_SCOUT_Q4_2025',
    'text',
    'earnings_guidance_text_candidate_scout_v1',
    'trading-model/storage/earnings_guidance_text_candidate_scout_q4_2025_20260515',
    'earnings_guidance_event_family;event_family_scouting_packet_v1;event_risk_governor;model_promotion',
    'sync_artifact',
    'Tenth itemized earnings/guidance scout: 12 official document text events, 11 candidate guidance-text events requiring review, one boilerplate-only event, zero accepted guidance interpretations, zero expectation baselines, and zero signed-direction-ready rows.'
  ),
  (
    'cfg_EGTCS001',
    'config',
    'EARNINGS_GUIDANCE_TEXT_CANDIDATE_REVIEW_GATE',
    'text',
    'candidate_guidance_text_requires_reviewed_interpretation_and_expectation_baseline',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'earnings_guidance_event_family;official_guidance_interpretation;signed_direction_claims;event_risk_governor',
    'sync_artifact',
    'Guidance/outlook-like candidate spans from official filings are review queue evidence only; safe-harbor, accounting, generic expectation, and risk language must not become signed claims without reviewed interpretation and expectation baselines.'
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
