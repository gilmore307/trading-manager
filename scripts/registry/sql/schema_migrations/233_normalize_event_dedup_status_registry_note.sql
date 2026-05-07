-- Normalize EVENT_DEDUP_STATUS note wording for classification-field policy.

UPDATE trading_registry
SET note = 'Classification value: stable lowercase token for event deduplication status such as canonical, covered_by_canonical_event, duplicate_of_canonical_event, related_followup, new_information, or unresolved. Covered duplicate news must not create independent event-factor alpha.'
WHERE key = 'EVENT_DEDUP_STATUS';
