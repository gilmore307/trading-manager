-- Register earnings/guidance official document-text coverage rerun.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_EGACS002',
    'term',
    'EARNINGS_GUIDANCE_ARTIFACT_COVERAGE_WITH_DOCUMENTS_Q4_2025',
    'text',
    'earnings_guidance_artifact_coverage_scout_v1',
    'trading-model/storage/earnings_guidance_artifact_coverage_with_documents_q4_2025_20260515',
    'earnings_guidance_event_family;event_family_scouting_packet_v1;event_risk_governor;model_promotion',
    'sync_artifact',
    'Ninth itemized earnings/guidance scout: bounded SEC document acquisition produced 12/12 official filing text artifacts, but guidance interpretation, expectation baselines, and signed-direction readiness remain zero.'
  ),
  (
    'cfg_EGACS002',
    'config',
    'EARNINGS_GUIDANCE_DOCUMENT_TEXT_NOT_SIGNED_CLAIM_GATE',
    'text',
    'official_document_text_requires_reviewed_guidance_interpretation_and_expectation_baseline',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'earnings_guidance_event_family;official_guidance_interpretation;signed_direction_claims;event_risk_governor',
    'sync_artifact',
    'Official filing/release/transcript text presence is necessary but insufficient: uninterpreted documents cannot establish beat/miss, guidance raise/cut, signed alpha, or stronger event-risk intervention evidence.'
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
