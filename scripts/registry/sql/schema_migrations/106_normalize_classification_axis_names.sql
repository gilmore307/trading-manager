-- Normalize classification field payloads around semantic axes rather than
-- context-specific or ambiguous wording.

UPDATE trading_registry
SET key = 'TASK_LIFECYCLE_STATUS',
    payload = 'task_lifecycle_status',
    note = 'canonical task lifecycle status field for task register and completion receipt slots. Classification value should use a stable lowercase token vocabulary unless the source contract explicitly requires another reviewed encoding.'
WHERE id = 'fld_5DVSJFM0';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'task_lifecycle_state', 'task_lifecycle_status'),
    key = replace(key, 'TASK_LIFECYCLE_STATE', 'TASK_LIFECYCLE_STATUS'),
    note = replace(note, 'task lifecycle state', 'task lifecycle status')
WHERE kind = 'status_value'
  AND applies_to LIKE '%task_lifecycle_state%';

UPDATE trading_registry
SET key = 'SECTOR_TYPE',
    payload = 'sector_type',
    note = 'issuer-published sector taxonomy label for an ETF holding constituent. Classification value should use a stable lowercase token vocabulary unless the source contract explicitly requires another reviewed encoding.'
WHERE id = 'fld_ETFH012';

UPDATE trading_registry
SET key = 'SOURCE_THEME_TAGS',
    payload = 'source_theme_tags',
    note = 'source-provided theme/tag labels used as event-extraction evidence, not a normalized model exposure classification. Classification value should use a stable lowercase token vocabulary unless the source contract explicitly requires another reviewed encoding.'
WHERE id = 'fld_GDLT008';

UPDATE trading_registry
SET key = 'EXPOSURE_TAGS',
    payload = 'exposure_tags',
    note = 'derived multi-label stock exposure tags such as semiconductor, AI, defensive, high_beta, or large_cap_growth. Classification value should use a stable lowercase token vocabulary unless the source contract explicitly requires another reviewed encoding.'
WHERE id = 'fld_STKEX008';
