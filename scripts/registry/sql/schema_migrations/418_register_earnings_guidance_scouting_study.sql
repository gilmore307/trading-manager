-- Register canonical earnings/guidance scouting study evidence.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_EGSS001',
    'script',
    'MODEL_EARNINGS_GUIDANCE_EVENT_SCOUTING_STUDY',
    'text',
    'PYTHONPATH=src python3 scripts/models/model_04_event_overlay/run_earnings_guidance_event_scouting.py',
    'trading-model/scripts/models/model_04_event_overlay/run_earnings_guidance_event_scouting.py',
    'earnings_guidance_event_family;event_family_scouting_packet_v1;activity_price_relationship_study;event_risk_governor',
    'sync_artifact',
    'Deterministic local study entrypoint that joins option-abnormality windows with reviewed Nasdaq earnings-calendar shells and filters matched controls to verified non-earnings dates. It performs no provider calls.'
  ),
  (
    'trm_EGSS001',
    'term',
    'EARNINGS_GUIDANCE_EVENT_SCOUTING_20260515',
    'text',
    'earnings_guidance_event_family_scouting_study_v1',
    'trading-model/storage/earnings_guidance_event_scouting_20260515',
    'earnings_guidance_event_family;event_family_scouting_packet_v1;event_activity_bridge;activity_price_relationship_study',
    'sync_artifact',
    'Canonical-calendar scouting artifact: 10 target-symbol earnings shells, 152 abnormal windows, 9 canonical earnings-shell windows across 2 symbols, and verified non-earnings controls for all windows. Diagnostic only; not promotion evidence.'
  ),
  (
    'cfg_EGSS001',
    'config',
    'EARNINGS_GUIDANCE_SCOUTING_CURRENT_STATUS',
    'text',
    'scouting_complete_for_calendar_shell_controls;pilot_training_blocked_pending_official_result_guidance_artifacts_and_verified_no_option_abnormality_controls',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'earnings_guidance_event_family;event_family_scouting_packet_v1;model_promotion',
    'sync_artifact',
    'Current status after canonical-calendar control pass. Event family remains scouting; coverage and verified option-control requirements block pilot training.'
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
