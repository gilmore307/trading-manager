-- Register web-discovered official source terms for calendars and ETF holdings.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('trm_B76OXHC5', 'term', 'FOMC_CALENDAR', 'text', 'Federal Reserve FOMC meeting calendar and related monetary policy event information', 'https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm', 'trading-data', 'official Federal Reserve source; no credential or secret alias required'),
  ('trm_THASHXK3', 'term', 'OFFICIAL_MACRO_RELEASE_CALENDAR', 'text', 'Official macroeconomic release calendars discovered through web search and confirmed against government or issuing-agency websites', NULL, 'trading-data', 'source-discovery rule rather than one provider URL; use web search to find current official agency pages and reject third-party calendars as source of truth unless explicitly approved as secondary references'),
  ('trm_LKP3RR2V', 'term', 'ETF_ISSUER_HOLDINGS', 'text', 'ETF holdings constituents and portfolio weights sourced from issuer websites or issuer-published holdings files', NULL, 'trading-data', 'issuer website is the source of truth for holdings and weights; third-party aggregators may not replace issuer data without explicit review')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;
