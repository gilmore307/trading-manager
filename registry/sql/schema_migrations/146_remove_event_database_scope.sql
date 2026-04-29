-- Remove the obsolete event_database scope token from active registry applies_to.
-- Event routing now uses concrete current boundaries such as 07_source_event_overlay
-- rather than an unregistered shared event_database concept.

UPDATE trading_registry
SET applies_to = NULLIF(
    trim(both ';' from replace(';' || coalesce(applies_to, '') || ';', ';event_database;', ';')),
    ''
)
WHERE applies_to LIKE '%event_database%';
