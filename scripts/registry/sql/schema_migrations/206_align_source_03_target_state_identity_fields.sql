-- Align source_03_target_state shared identity/temporal fields with the accepted
-- target-candidate keyed SQL shape now implemented in trading-data.

UPDATE trading_registry
SET applies_to = CASE
      WHEN applies_to IS NULL OR applies_to = '' THEN 'source_03_target_state'
      WHEN applies_to LIKE '%source_03_target_state%' THEN applies_to
      ELSE applies_to || ';source_03_target_state'
    END,
    note = 'Opaque anonymous row key for a TargetStateVectorModel candidate; source_03_target_state uses target_candidate_id as its natural key while real symbols remain audit/routing metadata outside model-facing vectors.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'TARGET_CANDIDATE_ID';

UPDATE trading_registry
SET applies_to = CASE
      WHEN applies_to IS NULL OR applies_to = '' THEN 'source_03_target_state'
      WHEN applies_to LIKE '%source_03_target_state%' THEN applies_to
      ELSE applies_to || ';source_03_target_state'
    END,
    note = 'Timestamp when evidence, source rows, feature rows, or model outputs became visible for point-in-time use. source_03_target_state carries available_time separately from observed data timestamp. Temporal value format: ISO 8601; normalized final outputs use America/New_York semantics unless explicitly reviewed otherwise.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'AVAILABLE_TIME';
