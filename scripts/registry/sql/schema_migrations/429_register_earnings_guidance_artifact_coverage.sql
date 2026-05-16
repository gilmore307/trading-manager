-- Register earnings/guidance official-artifact coverage scout and SEC filing-document saved output.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'dki_OFH0JXSP',
    'data_kind',
    'SEC_FILING_DOCUMENT',
    'text',
    'sec_filing_document',
    'trading-data/src/data_feed/08_feed_sec_company_financials',
    '08_feed_sec_company_financials;sec_company_financials;earnings_guidance_event_family;official_document_text',
    'sync_artifact',
    'Official SEC filing document metadata plus persisted text artifact, fetched by CIK, accession number, and document name for reviewed downstream result/guidance interpretation.'
  ),
  (
    'scr_EGACS001',
    'script',
    'MODEL_EARNINGS_GUIDANCE_ARTIFACT_COVERAGE_SCOUT',
    'text',
    'PYTHONPATH=src python3 scripts/models/model_04_event_overlay/run_earnings_guidance_artifact_coverage_scout.py',
    'trading-model/scripts/models/model_04_event_overlay/run_earnings_guidance_artifact_coverage_scout.py',
    'earnings_guidance_event_family;event_family_scouting_packet_v1;event_risk_governor;model_promotion',
    'sync_artifact',
    'Deterministic local coverage gate for official company filing/release/transcript text artifacts required before guidance interpretation; performs no provider calls.'
  ),
  (
    'trm_EGACS001',
    'term',
    'EARNINGS_GUIDANCE_ARTIFACT_COVERAGE_SCOUT_Q4_2025',
    'text',
    'earnings_guidance_artifact_coverage_scout_v1',
    'trading-model/storage/earnings_guidance_artifact_coverage_scout_q4_2025_20260515',
    'earnings_guidance_event_family;event_family_scouting_packet_v1;event_risk_governor;model_promotion',
    'sync_artifact',
    'Eighth itemized earnings/guidance scout: 12 SEC result filing references, but zero local official filing/release/transcript text artifacts, zero accepted guidance interpretations, zero expectation baselines, and zero signed-direction-ready rows.'
  ),
  (
    'cfg_EGACS001',
    'config',
    'EARNINGS_GUIDANCE_OFFICIAL_DOCUMENT_COVERAGE_GATE',
    'text',
    'requires_local_official_document_text_before_guidance_interpretation',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'earnings_guidance_event_family;official_guidance_interpretation;signed_direction_claims',
    'sync_artifact',
    'SEC filing metadata and normalized facts are not sufficient for guidance interpretation; missing official company document text must remain missing rather than inferred from price reaction or XBRL facts.'
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
