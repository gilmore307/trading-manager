-- Register same-symbol non-earnings option-control verification.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_SSNEOCV001',
    'script',
    'MODEL_SAME_SYMBOL_NON_EARNINGS_OPTION_CONTROL_VERIFICATION',
    'text',
    'PYTHONPATH=src python3 scripts/models/model_04_event_overlay/run_same_symbol_non_earnings_option_control_verification.py',
    'trading-model/scripts/models/model_04_event_overlay/run_same_symbol_non_earnings_option_control_verification.py',
    'earnings_guidance_event_family;option_derivatives_abnormality;event_family_scouting_packet_v1;activity_price_relationship_study;event_risk_governor',
    'sync_artifact',
    'Deterministic local summarizer for same-symbol non-earnings option-event receipt controls; records whether clean no-option-abnormality controls exist without making provider calls itself.'
  ),
  (
    'trm_SSNEOCV001',
    'term',
    'SAME_SYMBOL_NON_EARNINGS_OPTION_CONTROL_VERIFICATION_20260515',
    'text',
    'same_symbol_non_earnings_option_control_verification_v1',
    'trading-model/storage/same_symbol_non_earnings_option_control_verification_20260515',
    'earnings_guidance_event_family;option_derivatives_abnormality;event_family_scouting_packet_v1;activity_price_relationship_study;event_risk_governor',
    'sync_artifact',
    'Fifth itemized earnings/guidance scout: reused local option-matrix receipts for same-symbol non-earnings candidate controls; found zero verified no sampled option-abnormality controls across 24 candidates, so the earnings+option amplifier comparison remains blocked.'
  ),
  (
    'cfg_SSNEOCV001',
    'config',
    'SAME_SYMBOL_NON_EARNINGS_CONTROL_EXCLUSION_DAYS',
    'text',
    '3',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'earnings_guidance_event_family;option_derivatives_abnormality;model_promotion',
    'sync_artifact',
    'Same-symbol non-earnings option-control verification excludes candidate dates within plus/minus 3 calendar days of a same-symbol canonical Nasdaq earnings shell.'
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
