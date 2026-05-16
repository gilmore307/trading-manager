-- Register prior official guidance baseline source and document coverage.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_POGB001',
    'script',
    'MODEL_EARNINGS_GUIDANCE_PRIOR_OFFICIAL_BASELINE_SOURCE_AUDIT',
    'text',
    'PYTHONPATH=src python3 scripts/models/model_04_event_overlay/run_earnings_guidance_prior_official_baseline_audit.py',
    'trading-model/scripts/models/model_04_event_overlay/run_earnings_guidance_prior_official_baseline_audit.py',
    'earnings_guidance_event_family;prior_company_guidance;expectation_baseline;event_risk_governor',
    'sync_artifact',
    'No-provider model audit that consumes SEC submission rows and selects pre-event official filing candidates for prior-company-guidance baselines.'
  ),
  (
    'scr_POGB002',
    'script',
    'MODEL_EARNINGS_GUIDANCE_PRIOR_OFFICIAL_DOCUMENT_COVERAGE',
    'text',
    'PYTHONPATH=src python3 scripts/models/model_04_event_overlay/run_earnings_guidance_prior_official_document_coverage.py',
    'trading-model/scripts/models/model_04_event_overlay/run_earnings_guidance_prior_official_document_coverage.py',
    'earnings_guidance_event_family;prior_company_guidance;expectation_baseline;event_risk_governor',
    'sync_artifact',
    'No-provider coverage check that confirms selected prior official filing documents have local text artifacts before reviewed prior-guidance extraction.'
  ),
  (
    'trm_POGB001',
    'term',
    'EARNINGS_GUIDANCE_PRIOR_OFFICIAL_BASELINE_SOURCE_AUDIT_Q4_2025',
    'text',
    'earnings_guidance_prior_official_baseline_source_audit_v1',
    'trading-model/storage/earnings_guidance_prior_official_baseline_source_audit_q4_2025_20260515',
    'earnings_guidance_event_family;prior_company_guidance;expectation_baseline;event_risk_governor',
    'sync_artifact',
    'Fifteenth itemized source audit: selected 12/12 prior official SEC filing candidates after consuming bounded SEC submission artifacts; no signed claims unlocked.'
  ),
  (
    'trm_POGB002',
    'term',
    'EARNINGS_GUIDANCE_PRIOR_OFFICIAL_DOCUMENT_COVERAGE_Q4_2025',
    'text',
    'earnings_guidance_prior_official_document_coverage_v1',
    'trading-model/storage/earnings_guidance_prior_official_document_coverage_q4_2025_20260515',
    'earnings_guidance_event_family;prior_company_guidance;expectation_baseline;event_risk_governor',
    'sync_artifact',
    'Fifteenth itemized document coverage: 12/12 prior official document texts present, zero accepted prior-guidance baselines, zero signed-direction-ready rows.'
  ),
  (
    'cfg_POGB001',
    'config',
    'PRIOR_OFFICIAL_GUIDANCE_BASELINE_REVIEW_GATE',
    'text',
    'prior_official_document_text_present_uninterpreted_requires_reviewed_prior_guidance_extraction_before_guidance_surprise_claims',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'prior_company_guidance;expectation_baseline;signed_direction_claims;event_risk_governor',
    'sync_artifact',
    'Prior official document text coverage is necessary but not sufficient; guidance surprise remains blocked until reviewed prior-guidance baseline extraction and comparison exist.'
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
