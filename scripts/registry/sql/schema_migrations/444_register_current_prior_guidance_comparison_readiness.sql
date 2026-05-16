-- Register current-vs-prior earnings/guidance comparison readiness.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_CPGC001',
    'script',
    'MODEL_EARNINGS_GUIDANCE_CURRENT_PRIOR_COMPARISON_READINESS',
    'text',
    'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/run_earnings_guidance_current_prior_comparison_readiness.py',
    'trading-model/scripts/models/model_08_event_risk_governor/run_earnings_guidance_current_prior_comparison_readiness.py',
    'earnings_guidance_event_family;prior_company_guidance;current_guidance_comparison;event_risk_governor',
    'sync_artifact',
    'No-provider readiness pass that joins prior company-guidance context, current official guidance-context review rows, and official result artifacts before any raise/cut or signed-direction claim.'
  ),
  (
    'trm_CPGC001',
    'term',
    'EARNINGS_GUIDANCE_CURRENT_PRIOR_COMPARISON_READINESS_Q4_2025',
    'text',
    'earnings_guidance_current_prior_comparison_readiness_v1',
    'trading-model/storage/earnings_guidance_current_prior_comparison_readiness_q4_2025_20260516',
    'earnings_guidance_event_family;prior_company_guidance;current_guidance_comparison;event_risk_governor',
    'sync_artifact',
    'Eighteenth itemized scout: 7 accepted prior-guidance baseline events, 9 current partial guidance-context events, 0 current comparable guidance events, 0 accepted guidance raise/cut rows, and 0 signed-direction-ready rows.'
  ),
  (
    'cfg_CPGC001',
    'config',
    'CURRENT_PRIOR_GUIDANCE_COMPARISON_NON_CLAIM_POLICY',
    'text',
    'partial_current_future_operating_context_is_not_comparable_company_guidance_and_must_not_unlock_raise_cut_guidance_surprise_signed_alpha_or_event_risk_escalation',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'current_guidance_comparison;signed_direction_claims;event_risk_governor',
    'sync_artifact',
    'Primary-document partial guidance context remains direction-neutral until current earnings-release/exhibit/transcript guidance and PIT expectation baselines are accepted.'
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
