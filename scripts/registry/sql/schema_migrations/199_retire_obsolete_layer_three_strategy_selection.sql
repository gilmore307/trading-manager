-- Retire obsolete legacy Layer 3 strategy-selection registry surfaces.
-- Layer 3 active boundary is target-state construction:
-- source_03_target_state -> feature_03_target_state_vector -> model_03_target_state_vector.

DELETE FROM trading_registry
WHERE id IN (
  'dki_SSFE001',   -- FEATURE_03_STRATEGY_SELECTION
  'scr_F3SSGEN',  -- FEATURE_03_STRATEGY_SELECTION_GENERATE
  'trm_SSFR001',  -- STRATEGY_SELECTION_FEATURE_REQUEST
  'dbu_STRINPUT'  -- SOURCE_03_STRATEGY_SELECTION
);

UPDATE trading_registry
SET applies_to = btrim(
      regexp_replace(
        regexp_replace(';' || applies_to || ';', ';source_03_strategy_selection(?=;)', '', 'g'),
        ';+', ';', 'g'
      ),
      ';'
    ),
    updated_at = CURRENT_TIMESTAMP
WHERE applies_to LIKE '%source_03_strategy_selection%';

UPDATE trading_registry
SET note = '03 control-plane-facing target-local observed-input source contract for TargetStateVectorModel. Layer 3 data requests use source_03_target_state.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'dbu_TSTATE03';

UPDATE trading_registry
SET note = replace(note, 'these are state windows, not strategy variants.', 'these are state observation windows, not downstream action variants.'),
    updated_at = CURRENT_TIMESTAMP
WHERE id IN ('cfg_TSVW001', 'cfg_TSVWIN001')
  AND note LIKE '%strategy variants%';
