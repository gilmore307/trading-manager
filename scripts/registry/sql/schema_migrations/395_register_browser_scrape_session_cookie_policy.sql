-- Register shared policy for browser-scraped provider routes.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'term_BRWSCRAPE001',
    'term',
    'BROWSER_SCRAPE_SESSION_COOKIE_POLICY',
    'text',
    'browser_scrape_session_cookie_policy',
    'trading-manager/docs/81_decision.md;trading-data/docs/91_data_feed.md;trading-data/docs/93_feed_availability.md',
    'browser_scraped_source;provider_acquisition;cookie_session;trading_economics_calendar_web',
    'sync_artifact',
    'Browser-scraped provider routes keep authenticated browser session maintenance separate from normal bounded feed tasks, which consume exported local cookies and task-specific filters without per-task browser login or mutable-tab dependence.'
  ),
  (
    'cfg_BRWSCRAPE001',
    'config',
    'BROWSER_SCRAPE_COOKIE_SECRET_STORAGE',
    'text',
    '/root/secrets/<provider>-cookies.txt',
    'trading-manager/docs/81_decision.md;trading-data/docs/91_data_feed.md',
    'browser_scraped_source;secret_storage;cookie_session',
    'registry_only',
    'Local-only cookie jar location pattern for browser-scraped provider feeds. Cookie values remain outside Git and outside the registry.'
  )
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();
