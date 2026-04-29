-- Rename the source-secret field applies_to scope to describe what it is:
-- the schema of source-level secret files, not a file/kind named
-- source_secret_json.

UPDATE trading_registry
SET applies_to = replace(applies_to, 'source_secret_json', 'source_secret_file_schema')
WHERE applies_to IS NOT NULL
  AND applies_to LIKE '%source_secret_json%';

UPDATE trading_registry
SET note = replace(note, 'source_secret_json', 'source_secret_file_schema')
WHERE note IS NOT NULL
  AND note LIKE '%source_secret_json%';
