-- Remove the remaining active-registry note reference to the old event model surface name.

UPDATE trading_registry
SET note = 'Accepted EventRiskGovernor implementation surface for bounded event-risk evidence and intervention review. This is the active Layer 8 event-risk model surface.',
    updated_at = NOW()
WHERE key = 'MODEL_08_EVENT_RISK_GOVERNOR'
  AND note LIKE '%model_04_event_overlay%';
