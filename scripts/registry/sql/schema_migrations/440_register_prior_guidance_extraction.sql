-- Register prior official guidance baseline extraction.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_POGE001',
    'script',
    'MODEL_EARNINGS_GUIDANCE_PRIOR_GUIDANCE_EXTRACTION',
    'text',
    'PYTHONPATH=src python3 scripts/models/model_04_event_overlay/run_earnings_guidance_prior_guidance_extraction.py',
    'trading-model/scripts/models/model_04_event_overlay/run_earnings_guidance_prior_guidance_extraction.py',
    'earnings_guidance_event_family;prior_company_guidance;expectation_baseline;event_risk_governor',
    'sync_artifact',
    'No-provider extraction pass that accepts explicit prior official guidance/outlook context and rejects generic forward-looking boilerplate.'
  ),
  (
    'trm_POGE001',
    'term',
    'EARNINGS_GUIDANCE_PRIOR_GUIDANCE_EXTRACTION_Q4_2025',
    'text',
    'earnings_guidance_prior_guidance_extraction_v1',
    'trading-model/storage/earnings_guidance_prior_guidance_extraction_q4_2025_20260515',
    'earnings_guidance_event_family;prior_company_guidance;expectation_baseline;event_risk_governor',
    'sync_artifact',
    'Sixteenth itemized scout: 1 accepted prior-company-guidance baseline-context event, 3 accepted spans, 11 reviewed no prior guidance context, and zero signed-direction-ready rows.'
  ),
  (
    'cfg_POGE001',
    'config',
    'PRIOR_GUIDANCE_EXTRACTION_NON_CLAIM_POLICY',
    'text',
    'accepted_prior_guidance_context_is_baseline_evidence_not_guidance_surprise_signed_direction_alpha_or_event_risk_escalation',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'prior_company_guidance;expectation_baseline;signed_direction_claims;event_risk_governor',
    'sync_artifact',
    'Accepted prior-company-guidance context remains baseline evidence only until reviewed current guidance/result comparison and remaining baseline gates pass.'
  ),
  (
    'cfg_POGE002',
    'config',
    'PRIOR_GUIDANCE_SOURCE_SELECTION_REFINEMENT_GAP',
    'text',
    'selected_prior_official_filings_yielded_low_guidance_context_coverage_and_need_refinement_to_prior_earnings_or_outlook_bearing_documents',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'prior_company_guidance;expectation_baseline;source_selection;event_risk_governor',
    'sync_artifact',
    'Only 1/12 selected prior official filings contained accepted guidance context, so the source selection route needs refinement before broad signed earnings/guidance review.'
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
