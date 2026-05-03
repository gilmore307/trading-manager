-- Normalize helper script registry keys so the role/kind token sorts first.
-- Pattern: HELPER_<domain>_<action>, not <domain>_<action>_HELPER.

UPDATE trading_registry
SET key = CASE key
  WHEN 'BIGQUERY_REST_QUERY_HELPER' THEN 'HELPER_BIGQUERY_REST_QUERY'
  WHEN 'BRAVE_SEARCH_HELPER' THEN 'HELPER_BRAVE_SEARCH'
  WHEN 'REGISTRY_EXPORT_CURRENT_CSV_HELPER' THEN 'HELPER_REGISTRY_EXPORT_CURRENT_CSV'
  WHEN 'REGISTRY_GET_KEY_BY_ID_HELPER' THEN 'HELPER_REGISTRY_GET_KEY_BY_ID'
  WHEN 'REGISTRY_GET_PATH_BY_ID_HELPER' THEN 'HELPER_REGISTRY_GET_PATH_BY_ID'
  WHEN 'REGISTRY_GET_PAYLOAD_BY_ID_HELPER' THEN 'HELPER_REGISTRY_GET_PAYLOAD_BY_ID'
  WHEN 'REGISTRY_LOAD_SECRET_TEXT_BY_CONFIG_ID_HELPER' THEN 'HELPER_REGISTRY_LOAD_SECRET_TEXT_BY_CONFIG_ID'
  ELSE key
END,
applies_to = replace(applies_to, 'web_search_helper', 'helper_web_search'),
note = CASE
  WHEN note LIKE '%Helper key normalized 2026-04-29%' THEN note
  ELSE note || ' Helper key normalized 2026-04-29 to HELPER_<domain>_<action> ordering.'
END
WHERE kind = 'script'
AND key IN (
  'BIGQUERY_REST_QUERY_HELPER',
  'BRAVE_SEARCH_HELPER',
  'REGISTRY_EXPORT_CURRENT_CSV_HELPER',
  'REGISTRY_GET_KEY_BY_ID_HELPER',
  'REGISTRY_GET_PATH_BY_ID_HELPER',
  'REGISTRY_GET_PAYLOAD_BY_ID_HELPER',
  'REGISTRY_LOAD_SECRET_TEXT_BY_CONFIG_ID_HELPER'
);

UPDATE trading_registry
SET applies_to = replace(applies_to, 'web_search_helper', 'helper_web_search')
WHERE applies_to IS NOT NULL
AND applies_to LIKE '%web_search_helper%';
