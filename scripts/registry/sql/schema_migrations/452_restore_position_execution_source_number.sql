-- Restore the selected-contract position-execution data source number.
-- This source id is 06 and is not part of the model-layer renumbering.

UPDATE trading_registry
SET payload = replace(payload, 'source_05_position_execution', 'source_06_position_execution'),
    path = replace(path, 'source_05_position_execution', 'source_06_position_execution'),
    applies_to = replace(applies_to, 'source_05_position_execution', 'source_06_position_execution'),
    note = replace(note, 'source_05_position_execution', 'source_06_position_execution'),
    updated_at = NOW()
WHERE payload LIKE '%source_05_position_execution%'
   OR path LIKE '%source_05_position_execution%'
   OR applies_to LIKE '%source_05_position_execution%'
   OR note LIKE '%source_05_position_execution%';
