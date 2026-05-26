-- Canonicalize duplicated abnormal-activity family and activity-price proof
-- gate payloads.
--
-- Keep the existing semantic rows for their local gate/check meanings, but
-- move duplicated literal value sets into canonical config rows.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_AAEFS001',
    'config',
    'ABNORMAL_ACTIVITY_EVIDENCE_FAMILY_SET',
    'text',
    'price_action_pattern;residual_market_structure_disturbance;microstructure_liquidity_disruption;option_derivatives_abnormality',
    'trading-model/docs/19_layer_10_event_risk_governor.md;trading-model/docs/50_activity_price_relationship_study.md',
    'abnormal_activity;event_activity_bridge;event_risk_governor;activity_price_relationship_study',
    'sync_artifact',
    'Canonical abnormal-activity evidence family set for residual/provenance/risk evidence and coverage gates. These families must not duplicate ordinary model-owned bars, liquidity, trend, or target-state features.'
  ),
  (
    'cfg_APRGR001',
    'config',
    'ACTIVITY_PRICE_RELATIONSHIP_PROOF_GATE_REQUIREMENT',
    'text',
    'required_before_event_activity_bridge_model_promotion',
    'trading-model/docs/19_layer_10_event_risk_governor.md;trading-model/docs/50_activity_price_relationship_study.md',
    'activity_price_relationship_proof_gate;event_activity_bridge;event_risk_governor;model_promotion',
    'sync_artifact',
    'Canonical requirement token for proving stable point-in-time activity-price relationships before EventActivityBridge promotion or risk-intervention use.'
  )
ON CONFLICT (id) DO UPDATE SET
    kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();

UPDATE trading_registry
SET payload = 'abnormal_activity_evidence_family_set',
    note = 'Coverage completion gate consumes ABNORMAL_ACTIVITY_EVIDENCE_FAMILY_SET; all canonical abnormal-activity families must be represented before directional or promotion judgment.',
    updated_at = NOW()
WHERE key = 'ABNORMALITY_COVERAGE_COMPLETE_REQUIRED_FAMILIES';

UPDATE trading_registry
SET payload = 'abnormal_activity_evidence_family_set',
    note = 'Event abnormal-activity categorization consumes ABNORMAL_ACTIVITY_EVIDENCE_FAMILY_SET for implementation-facing classification.',
    updated_at = NOW()
WHERE key = 'EVENT_ABNORMAL_ACTIVITY_EVIDENCE_CATEGORIES';

UPDATE trading_registry
SET payload = 'activity_price_relationship_proof_gate_requirement',
    note = 'Cross-section study consumes ACTIVITY_PRICE_RELATIONSHIP_PROOF_GATE_REQUIREMENT and must span size buckets, sector/theme buckets, and event families; one story stock is insufficient for model-layer promotion.',
    updated_at = NOW()
WHERE key = 'ACTIVITY_PRICE_CROSS_SECTION_STUDY_REQUIRED';

UPDATE trading_registry
SET payload = 'activity_price_relationship_proof_gate_requirement',
    note = 'Activity-price proof gate consumes ACTIVITY_PRICE_RELATIONSHIP_PROOF_GATE_REQUIREMENT before abnormal activity can become a separate model layer or risk-intervention input.',
    updated_at = NOW()
WHERE key = 'ACTIVITY_PRICE_RELATIONSHIP_PROOF_GATE';
