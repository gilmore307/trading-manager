-- Clarify that generated event ids preserve the legacy base and use disambiguators only on collisions.

UPDATE trading_registry
SET payload = 'base:event_category_type;event_time;symbol;reference|collision_disambiguator:source_name;title_or_headline',
    note = 'Generated source_04_event_overlay event ids keep the legacy base of category, time, symbol, and reference. When that base collides inside a batch, source name plus title/headline deterministically disambiguate same-timestamp events such as core CPI and CPI.',
    updated_at = NOW()
WHERE id = 'cfg_EVTID001';
