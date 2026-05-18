-- Include approved calendar shells in the source-priority vocabulary.

UPDATE trading_registry
SET payload = 'official_disclosure;official_data_release;company_disclosure;regulatory_disclosure;approved_calendar;source_detector;verified_news;broad_news;derivative_news;unknown',
    path = 'trading-data/src/data_source/source_09_event_risk_governor/README.md',
    applies_to = 'source_09_event_risk_governor;event_risk_governor;event_context_vector;calendar_discovery;scheduled_macro_release',
    note = 'Allowed source_priority values for canonical-event selection. Official disclosure/data rows outrank approved calendar shells; approved calendar rows may represent scheduled releases but must not carry result facts until released; browser/agent article reading may support classification but does not change source priority by itself.',
    updated_at = NOW()
WHERE id = 'cfg_EVD002'
  AND kind = 'config'
  AND key = 'EVENT_SOURCE_PRIORITY_VALUES';
