-- Register earnings/guidance sampled option-control verification.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_EOCV001',
    'script',
    'MODEL_EARNINGS_OPTION_CONTROL_VERIFICATION',
    'text',
    'PYTHONPATH=src python3 scripts/models/model_04_event_overlay/run_earnings_option_control_verification.py',
    'trading-model/scripts/models/model_04_event_overlay/run_earnings_option_control_verification.py',
    'earnings_guidance_event_family;option_derivatives_abnormality;event_family_scouting_packet_v1;activity_price_relationship_study;event_risk_governor',
    'sync_artifact',
    'Deterministic local summarizer for contract-level earnings option-event probes; records whether sampled earnings-without-option-abnormality controls exist without making provider calls itself.'
  ),
  (
    'trm_EOCV001',
    'term',
    'EARNINGS_OPTION_NO_ABNORMALITY_CONTROL_PROBE_20260515',
    'text',
    'earnings_option_control_verification_v1',
    'trading-model/storage/earnings_option_no_abnormality_control_probe_20260515',
    'earnings_guidance_event_family;option_derivatives_abnormality;event_family_scouting_packet_v1;activity_price_relationship_study;event_risk_governor',
    'sync_artifact',
    'Fourth itemized earnings/guidance scout: sampled five candidate strikes and both CALL/PUT for earnings rows missing option coverage; found zero verified no sampled option-abnormality controls, so amplifier comparison remains blocked.'
  ),
  (
    'cfg_EOCV001',
    'config',
    'SAMPLED_OPTION_ABNORMALITY_CONTROL_SCOPE',
    'text',
    'sampled_contract_set_not_full_option_chain',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'earnings_guidance_event_family;option_derivatives_abnormality;model_promotion',
    'sync_artifact',
    'No-option-abnormality verification from the current probe covers only the sampled contract set under the option-event standard, not the full option chain; promotion or amplifier claims still require matched clean controls.'
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
