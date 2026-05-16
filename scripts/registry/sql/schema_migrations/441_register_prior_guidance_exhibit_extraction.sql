-- Register prior earnings-exhibit guidance baseline extraction.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_PGEE001',
    'script',
    'MODEL_EARNINGS_GUIDANCE_PRIOR_GUIDANCE_EXHIBIT_EXTRACTION',
    'text',
    'PYTHONPATH=src python3 scripts/models/model_04_event_overlay/run_earnings_guidance_prior_guidance_exhibit_extraction.py',
    'trading-model/scripts/models/model_04_event_overlay/run_earnings_guidance_prior_guidance_exhibit_extraction.py',
    'earnings_guidance_event_family;prior_company_guidance;expectation_baseline;event_risk_governor',
    'sync_artifact',
    'No-provider extraction pass that reviews official prior-quarter earnings/outlook exhibits for prior-company-guidance baseline context.'
  ),
  (
    'trm_PGEE001',
    'term',
    'EARNINGS_GUIDANCE_PRIOR_GUIDANCE_EXHIBIT_EXTRACTION_Q4_2025',
    'text',
    'earnings_guidance_prior_guidance_exhibit_extraction_v1',
    'trading-model/storage/earnings_guidance_prior_guidance_exhibit_extraction_q4_2025_20260515',
    'earnings_guidance_event_family;prior_company_guidance;expectation_baseline;event_risk_governor',
    'sync_artifact',
    'Seventeenth itemized scout: 7 accepted prior-company-guidance baseline-context events, 8 accepted exhibit documents, 42 accepted spans, 5 reviewed no prior guidance context events, and zero signed-direction-ready rows.'
  ),
  (
    'cfg_PGEE001',
    'config',
    'PRIOR_GUIDANCE_EXHIBIT_EXTRACTION_NON_CLAIM_POLICY',
    'text',
    'accepted_prior_earnings_exhibit_guidance_context_is_baseline_evidence_not_guidance_surprise_signed_direction_alpha_or_event_risk_escalation',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'prior_company_guidance;expectation_baseline;signed_direction_claims;event_risk_governor',
    'sync_artifact',
    'Prior earnings-exhibit guidance spans are accepted baseline context only until current guidance/result comparison and remaining baseline gates pass.'
  ),
  (
    'cfg_PGEE002',
    'config',
    'PRIOR_GUIDANCE_SOURCE_SELECTION_EXHIBIT_ROUTE',
    'text',
    'prior_company_guidance_source_selection_should_target_prior_earnings_or_outlook_bearing_exhibits_not_primary_8k_wrappers_or_arbitrary_nearby_filings',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'prior_company_guidance;expectation_baseline;source_selection;event_risk_governor',
    'sync_artifact',
    'The exhibit-level route improved accepted prior-guidance baseline context from 1/12 to 7/12 events in the diagnostic slice.'
  ),
  (
    'cfg_PGEE003',
    'config',
    'REVENUE_CONSENSUS_ROUTE_CANDIDATE_POLICY',
    'text',
    'trading_economics_earnings_revenue_consensus_is_future_route_candidate_until_pre_event_persisted_baseline_artifacts_exist',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'revenue_consensus;expectation_baseline;earnings_guidance_event_family;event_risk_governor',
    'sync_artifact',
    'Trading Economics earnings pages expose revenue-consensus-like fields, but historical signed claims remain blocked until accepted pre-event persisted revenue-consensus baseline artifacts exist.'
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
