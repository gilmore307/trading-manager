-- Register earnings/guidance plus option-abnormality split scout.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_EOAS001',
    'script',
    'MODEL_EARNINGS_OPTION_ABNORMALITY_SPLIT_SCOUT',
    'text',
    'PYTHONPATH=src python3 scripts/models/model_04_event_overlay/run_earnings_option_abnormality_split_scout.py',
    'trading-model/scripts/models/model_04_event_overlay/run_earnings_option_abnormality_split_scout.py',
    'earnings_guidance_event_family;option_derivatives_abnormality;event_family_scouting_packet_v1;activity_price_relationship_study;event_risk_governor',
    'sync_artifact',
    'Deterministic local study entrypoint that joins canonical earnings shells to reviewed option-abnormality evidence and blocks the amplifier claim when verified earnings-without-option-abnormality controls are absent.'
  ),
  (
    'trm_EOAS001',
    'term',
    'EARNINGS_OPTION_ABNORMALITY_SPLIT_SCOUT_20260515',
    'text',
    'earnings_option_abnormality_split_scout_v1',
    'trading-model/storage/earnings_option_abnormality_split_scout_20260515',
    'earnings_guidance_event_family;option_derivatives_abnormality;event_family_scouting_packet_v1;activity_price_relationship_study;event_risk_governor',
    'sync_artifact',
    'Third itemized earnings/guidance scout: existing reviewed option matrix overlapped two canonical earnings rows, both with verified option abnormality and zero verified earnings-without-option-abnormality controls; amplifier comparison remains blocked.'
  ),
  (
    'cfg_EOAS001',
    'config',
    'EARNINGS_OPTION_ABNORMALITY_AMPLIFIER_BLOCKER',
    'text',
    'requires_matched_earnings_without_option_abnormality_controls_under_same_option_event_standard',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'earnings_guidance_event_family;option_derivatives_abnormality;model_promotion',
    'sync_artifact',
    'Earnings plus option-abnormality amplifier claims remain blocked until the comparison includes matched earnings dates with verified no-option-abnormality coverage under the same option-event standard.'
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
