-- Normalize remaining timestamp fields discovered during field-like audit.
-- Temporal values must live in temporal_field, and identical generated-at semantics
-- should share one field row with usage in applies_to.

DELETE FROM trading_registry
WHERE id = 'fld_OPD047';

UPDATE trading_registry
SET kind = 'temporal_field',
    key = 'GENERATED_AT_ET',
    payload_format = 'field_name',
    payload = 'generated_at_et',
    applies_to = 'event_analysis_report_template;option_activity_event_detail_template',
    note = 'canonical America/New_York timestamp when an analysis report, standard snapshot, or generated artifact was produced. Temporal value format: ISO 8601; dates use YYYY-MM-DD and datetimes/times include explicit timezone or ET suffix semantics.'
WHERE id = 'fld_EVT037';

UPDATE trading_registry
SET kind = 'temporal_field',
    payload_format = 'field_name',
    note = 'GDELT article observation timestamp normalized to UTC. Temporal value format: ISO 8601; dates use YYYY-MM-DD and datetimes/times include explicit timezone or UTC suffix semantics.'
WHERE id = 'fld_GDLT002';

UPDATE trading_registry
SET kind = 'temporal_field',
    note = 'interval start timestamp in America/New_York for interval aggregate outputs. Temporal value format: ISO 8601; dates use YYYY-MM-DD and datetimes/times include explicit timezone or ET suffix semantics.'
WHERE id = 'fld_MKT002';
