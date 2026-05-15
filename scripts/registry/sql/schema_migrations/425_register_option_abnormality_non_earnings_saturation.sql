-- Register option-abnormality non-earnings saturation diagnostic.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_OANS001',
    'script',
    'MODEL_OPTION_ABNORMALITY_NON_EARNINGS_SATURATION',
    'text',
    'PYTHONPATH=src python3 scripts/models/model_04_event_overlay/run_option_abnormality_non_earnings_saturation.py',
    'trading-model/scripts/models/model_04_event_overlay/run_option_abnormality_non_earnings_saturation.py',
    'option_derivatives_abnormality;earnings_guidance_event_family;activity_price_relationship_study;event_risk_governor',
    'sync_artifact',
    'Deterministic local diagnostic that checks whether reviewed non-earnings symbol/date windows can furnish clean no-option-abnormality controls under the current option-event standard.'
  ),
  (
    'trm_OANS001',
    'term',
    'OPTION_ABNORMALITY_NON_EARNINGS_SATURATION_20260515',
    'text',
    'option_abnormality_non_earnings_saturation_v1',
    'trading-model/storage/option_abnormality_non_earnings_saturation_20260515',
    'option_derivatives_abnormality;earnings_guidance_event_family;activity_price_relationship_study;event_risk_governor',
    'sync_artifact',
    'Fifth itemized earnings/guidance scout: 34 reviewed same-symbol non-earnings windows all emitted complete option-abnormality events, proving the current option-event standard is saturated for no-abnormality control design in this sample.'
  ),
  (
    'cfg_OANS001',
    'config',
    'OPTION_ABNORMALITY_STANDARD_SATURATION_BLOCKER',
    'text',
    'current_option_event_standard_saturated_no_clean_non_earnings_controls',
    'trading-model/docs/99_activity_price_relationship_study.md',
    'option_derivatives_abnormality;earnings_guidance_event_family;model_promotion',
    'sync_artifact',
    'Current option-event standard must not be used for earnings+option amplifier promotion because it emitted complete abnormality events across all reviewed non-earnings windows in the matrix sample.'
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
