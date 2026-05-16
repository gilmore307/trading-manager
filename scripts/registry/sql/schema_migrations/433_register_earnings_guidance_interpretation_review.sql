-- Register earnings/guidance official interpretation review.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_EGIR001',
    'script',
    'MODEL_EARNINGS_GUIDANCE_INTERPRETATION_REVIEW',
    'text',
    'PYTHONPATH=src python3 scripts/models/model_04_event_overlay/run_earnings_guidance_interpretation_review.py',
    'trading-model/scripts/models/model_04_event_overlay/run_earnings_guidance_interpretation_review.py',
    'earnings_guidance_event_family;event_family_scouting_packet_v1;event_risk_governor;model_promotion',
    'sync_artifact',
    'Deterministic local review that separates partial official guidance context from rejected boilerplate/accounting/risk language; performs no provider calls and makes no signed claims.'
  ),
  (
    'trm_EGIR001',
    'term',
    'EARNINGS_GUIDANCE_INTERPRETATION_REVIEW_Q4_2025',
    'text',
    'earnings_guidance_interpretation_review_v1',
    'trading-model/storage/earnings_guidance_interpretation_review_q4_2025_20260515',
    'earnings_guidance_event_family;event_family_scouting_packet_v1;event_risk_governor;model_promotion',
    'sync_artifact',
    'Eleventh itemized earnings/guidance scout: 9 partial official guidance-context events, 3 reviewed no accepted guidance-context events, zero accepted guidance raise/cut rows, zero expectation baselines, and zero signed-direction-ready rows.'
  ),
  (
    'cfg_EGIR001',
    'config',
    'EARNINGS_GUIDANCE_PARTIAL_CONTEXT_NOT_SIGNED_DIRECTION_GATE',
    'text',
    'partial_guidance_context_requires_expectation_baseline_before_signed_claims',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'earnings_guidance_event_family;official_guidance_interpretation;signed_direction_claims;event_risk_governor',
    'sync_artifact',
    'Partial official future operating/financial context is direction-neutral event context only; guidance raise/cut, beat/miss, signed alpha, model activation, and stronger event-risk interventions remain blocked without point-in-time expectation baselines.'
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
