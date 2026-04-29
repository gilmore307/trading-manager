UPDATE trading_registry
SET payload_format = 'field_name',
    note = 'Identity value: canonical normalized option contract symbol used after contract identity is known or reconstructable',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'OPTION_SYMBOL';

UPDATE trading_registry
SET payload_format = 'field_name',
    note = 'Path value: primary locator for event details; may be a web URL, SEC file path, or internal artifact path',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'EVENT_REFERENCE';

UPDATE trading_registry
SET payload_format = 'field_name',
    note = 'Classification value: stable lowercase token for ' || payload || '.',
    updated_at = CURRENT_TIMESTAMP
WHERE key IN ('SNAPSHOT_TYPE', 'INFORMATION_ROLE_TYPE', 'EVENT_CATEGORY_TYPE', 'SCOPE_TYPE', 'REFERENCE_TYPE');

UPDATE trading_registry
SET payload_format = 'field_name',
    updated_at = CURRENT_TIMESTAMP
WHERE key IN ('DOLLAR_VOLUME', 'QUOTE_AVG_BID_SIZE', 'QUOTE_AVG_ASK_SIZE', 'QUOTE_SPREAD_BPS');
