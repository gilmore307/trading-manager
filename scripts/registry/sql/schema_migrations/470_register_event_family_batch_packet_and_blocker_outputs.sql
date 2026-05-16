-- Register explicit first-pass packet and blocker queue outputs for the event-family batch catalog.

UPDATE trading_registry
SET applies_to = 'event_family_batch_catalog_v1;event_family_batch_summary_v1;event_family_batch_queue;event_family_first_pass_packet_v1;event_family_blocker_queue;event_family_scouting;model_08_event_risk_governor;fine_grained_event_family_association',
    note = 'Builds the non-mutating fine-grained event-family batch catalog for Layer 8 EventRiskGovernor association scouting. Routing buckets such as symbol_news, sector_news, macro_news, sec_filing, and earnings_guidance are split into mechanism-level first-pass family packets, a priority queue, and blocker queue before any price/path association study, risk promotion, or alpha claim. The helper performs no provider calls, model activation, broker/account mutation, or artifact deletion.',
    updated_at = NOW()
WHERE id = 'scr_M8ERGFAM001';
