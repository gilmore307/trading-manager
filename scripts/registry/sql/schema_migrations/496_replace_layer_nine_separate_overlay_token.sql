-- Replace stale registry applicability wording that could imply Layer 9 is outside
-- the historical-modeling system service. Layer 9 remains a distinct overlay lane,
-- but it is service-owned.

UPDATE trading_registry
SET applies_to = replace(applies_to, 'event_risk_governor_separate', 'event_risk_governor_overlay_lane'),
    note = replace(note, 'separate Layer 9 event-risk overlay', 'service-owned Layer 9 event-risk overlay lane'),
    updated_at = NOW()
WHERE applies_to LIKE '%event_risk_governor_separate%'
   OR note LIKE '%separate Layer 9 event-risk overlay%';
